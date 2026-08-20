/*
Exact O(n^2) no-three-in-line verifier for hilbert-193-500k.jsonl.

For each vertex k, canonicalize the primitive integer directions to every
earlier vertex. A duplicate direction is equivalent to a collinear triple
(i,j,k). Four fixed stripes cover every pair exactly once. Progress is logged
once per minute; SIGINT/SIGTERM writes an atomic, artifact-bound checkpoint.

Build:
  clang++ -O3 -std=c++17 -pthread verify_hilbert_exhaustive.cpp \
    -o verify_hilbert_exhaustive
Run:
  ./verify_hilbert_exhaustive hilbert-193-500k.jsonl
*/
#include <algorithm>
#include <atomic>
#include <chrono>
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

struct Point { int x, y, z; };
static constexpr int VERSION = 1;
static constexpr int WORKERS = 4;
static std::atomic<bool> stop_requested{false};

static void on_signal(int) { stop_requested.store(true, std::memory_order_relaxed); }

static std::string timestamp() {
  const auto now = std::chrono::system_clock::now();
  const std::time_t t = std::chrono::system_clock::to_time_t(now);
  std::tm tm{};
  gmtime_r(&t, &tm);
  char out[32];
  std::strftime(out, sizeof(out), "%Y-%m-%dT%H:%M:%SZ", &tm);
  return out;
}

static uint64_t fnv1a(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) throw std::runtime_error("cannot open artifact: " + path);
  uint64_t h = 1469598103934665603ULL;
  char buf[1 << 20];
  while (in) {
    in.read(buf, sizeof(buf));
    const auto count = in.gcount();
    for (std::streamsize i = 0; i < count; ++i) {
      h ^= static_cast<unsigned char>(buf[i]);
      h *= 1099511628211ULL;
    }
  }
  return h;
}

static int field(const std::string& line, const char* name) {
  const std::string needle = std::string("\"") + name + "\":";
  const auto pos = line.find(needle);
  if (pos == std::string::npos) throw std::runtime_error("missing field " + std::string(name));
  std::size_t used = 0;
  const int value = std::stoi(line.substr(pos + needle.size()), &used);
  if (!used) throw std::runtime_error("invalid integer field " + std::string(name));
  return value;
}

static std::vector<Point> load_points(const std::string& path, std::size_t limit) {
  std::ifstream in(path);
  if (!in) throw std::runtime_error("cannot open artifact: " + path);
  std::vector<Point> points;
  points.reserve(limit);
  std::string line;
  while (points.size() < limit && std::getline(in, line)) {
    const int expected_i = static_cast<int>(points.size());
    if (field(line, "i") != expected_i) throw std::runtime_error("nonconsecutive row index");
    Point p{field(line, "x"), field(line, "y"), field(line, "z")};
    if (!points.empty() && p.z <= points.back().z) throw std::runtime_error("z coordinate is not strictly increasing");
    points.push_back(p);
  }
  if (points.size() != limit) throw std::runtime_error("artifact shorter than requested vertex count");
  return points;
}

static uint64_t mix(uint64_t x) {
  x += 0x9e3779b97f4a7c15ULL;
  x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
  x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
  return x ^ (x >> 31);
}

static uint64_t direction_key(const Point& earlier, const Point& apex) {
  int64_t x = static_cast<int64_t>(earlier.x) - apex.x;
  int64_t y = static_cast<int64_t>(earlier.y) - apex.y;
  int64_t z = static_cast<int64_t>(earlier.z) - apex.z;
  const int64_t g = std::gcd(std::gcd(std::llabs(x), std::llabs(y)), std::llabs(z));
  if (!g) throw std::runtime_error("repeated vertex");
  x /= g; y /= g; z /= g;
  if (x < 0 || (x == 0 && (y < 0 || (y == 0 && z < 0)))) { x = -x; y = -y; z = -z; }
  constexpr int64_t XY = 1 << 12;
  constexpr int64_t Z = 1 << 23;
  if (x < -XY || x >= XY || y < -XY || y >= XY || z < -Z || z >= Z)
    throw std::runtime_error("direction packing bound exceeded");
  return (static_cast<uint64_t>(x + XY) << 37) |
         (static_cast<uint64_t>(y + XY) << 24) |
         static_cast<uint64_t>(z + Z);
}

struct DirectionSet {
  std::vector<uint64_t> keys;
  std::vector<uint32_t> epochs;
  std::vector<int> owners;
  uint32_t epoch = 0;
  std::size_t mask;

  explicit DirectionSet(std::size_t maximum) {
    std::size_t capacity = 1;
    while (capacity < maximum * 2) capacity <<= 1;
    keys.resize(capacity);
    epochs.assign(capacity, 0);
    owners.resize(capacity);
    mask = capacity - 1;
  }

  void clear() {
    if (++epoch == 0) { std::fill(epochs.begin(), epochs.end(), 0); epoch = 1; }
  }

  int insert(uint64_t key, int owner) {
    std::size_t slot = mix(key) & mask;
    while (epochs[slot] == epoch) {
      if (keys[slot] == key) return owners[slot];
      slot = (slot + 1) & mask;
    }
    epochs[slot] = epoch;
    keys[slot] = key;
    owners[slot] = owner;
    return -1;
  }
};

struct Metadata {
  uint64_t bytes = 0, fnv = 0;
  std::size_t vertices = 0;
};

static uint64_t pairs_before(std::size_t next, int worker) {
  if (next <= static_cast<std::size_t>(worker)) return 0;
  const uint64_t count = (next - 1 - worker) / WORKERS + 1;
  const uint64_t last = worker + (count - 1) * WORKERS;
  return count * (worker + last) / 2;
}

static void write_checkpoint(const std::string& path, const Metadata& meta,
                             const std::vector<std::atomic<std::size_t>>& next) {
  const std::string tmp = path + ".tmp";
  std::ofstream out(tmp, std::ios::trunc);
  if (!out) throw std::runtime_error("cannot write checkpoint");
  out << VERSION << ' ' << WORKERS << ' ' << meta.vertices << ' ' << meta.bytes << ' ' << meta.fnv;
  for (int w = 0; w < WORKERS; ++w) out << ' ' << next[w].load(std::memory_order_relaxed);
  out << '\n';
  out.close();
  std::filesystem::rename(tmp, path);
}

static bool read_checkpoint(const std::string& path, const Metadata& meta,
                            std::vector<std::atomic<std::size_t>>& next) {
  std::ifstream in(path);
  if (!in) return false;
  int version = 0, workers = 0;
  Metadata saved;
  in >> version >> workers >> saved.vertices >> saved.bytes >> saved.fnv;
  if (!in || version != VERSION || workers != WORKERS || saved.vertices != meta.vertices ||
      saved.bytes != meta.bytes || saved.fnv != meta.fnv)
    throw std::runtime_error("checkpoint metadata mismatch; remove it for a fresh run");
  for (int w = 0; w < WORKERS; ++w) {
    std::size_t value;
    in >> value;
    if (!in || value < static_cast<std::size_t>(w) || value > meta.vertices + WORKERS)
      throw std::runtime_error("invalid checkpoint progress");
    next[w].store(value, std::memory_order_relaxed);
  }
  return true;
}

static void append_log(const std::string& path, const std::string& text) {
  std::ofstream out(path, std::ios::app);
  out << timestamp() << ' ' << text << '\n';
  out.flush();
}

int main(int argc, char** argv) try {
  if (argc < 2 || argc > 6) {
    std::cerr << "usage: " << argv[0] << " ARTIFACT [VERTICES [CHECKPOINT [LOG [FRESH]]]]\n";
    return 2;
  }
  const std::string artifact = argv[1];
  const std::size_t vertices = argc >= 3 ? std::stoull(argv[2]) : 500001;
  const std::string checkpoint = argc >= 4 ? argv[3] : "logs/hilbert-193-500k.exhaustive.ckpt";
  const std::string log_path = argc >= 5 ? argv[4] : "logs/hilbert-193-500k.exhaustive.log";
  const bool fresh = argc >= 6 && std::string(argv[5]) == "fresh";
  if (vertices < 3) throw std::runtime_error("need at least three vertices");
  std::filesystem::create_directories(std::filesystem::path(checkpoint).parent_path());
  if (fresh) std::filesystem::remove(checkpoint);

  Metadata meta{std::filesystem::file_size(artifact), fnv1a(artifact), vertices};
  const auto points = load_points(artifact, vertices);
  int min_x = points[0].x, max_x = points[0].x, min_y = points[0].y, max_y = points[0].y;
  for (const auto& p : points) {
    min_x = std::min(min_x, p.x); max_x = std::max(max_x, p.x);
    min_y = std::min(min_y, p.y); max_y = std::max(max_y, p.y);
  }
  if (max_x - min_x >= (1 << 12) || max_y - min_y >= (1 << 12) ||
      static_cast<int64_t>(points.back().z) - points.front().z >= (1 << 23))
    throw std::runtime_error("coordinate span exceeds direction packing bounds");

  std::vector<std::atomic<std::size_t>> next(WORKERS);
  for (int w = 0; w < WORKERS; ++w) next[w].store(w, std::memory_order_relaxed);
  const bool resumed = read_checkpoint(checkpoint, meta, next);
  std::signal(SIGINT, on_signal);
  std::signal(SIGTERM, on_signal);

  std::atomic<bool> failed{false};
  std::atomic<int> done{0};
  std::atomic<int> wi{-1}, wj{-1}, wk{-1};
  const uint64_t total_pairs = static_cast<uint64_t>(vertices) * (vertices - 1) / 2;
  const auto started = std::chrono::steady_clock::now();
  append_log(log_path, std::string(resumed ? "resume" : "start") + " vertices=" + std::to_string(vertices) +
      " pairs=" + std::to_string(total_pairs) + " workers=4 checkpoint=" + checkpoint);
  std::cout << "EXHAUSTIVE STARTED vertices=" << vertices << " pairs=" << total_pairs
            << " workers=4 resumed=" << resumed << std::endl;

  std::vector<std::thread> threads;
  for (int w = 0; w < WORKERS; ++w) {
    threads.emplace_back([&, w] {
      DirectionSet seen(vertices);
      for (std::size_t k = next[w].load(); k < vertices && !stop_requested.load() && !failed.load(); k += WORKERS) {
        seen.clear();
        for (std::size_t i = 0; i < k; ++i) {
          const uint64_t key = direction_key(points[i], points[k]);
          const int prior = seen.insert(key, static_cast<int>(i));
          if (prior >= 0) {
            wi.store(prior); wj.store(static_cast<int>(i)); wk.store(static_cast<int>(k));
            failed.store(true);
            break;
          }
        }
        if (!failed.load()) next[w].store(k + WORKERS, std::memory_order_relaxed);
      }
      done.fetch_add(1);
    });
  }

  auto last_report = started - std::chrono::minutes(2);
  while (done.load() != WORKERS) {
    std::this_thread::sleep_for(std::chrono::seconds(1));
    const auto now = std::chrono::steady_clock::now();
    if (now - last_report >= std::chrono::seconds(60) || stop_requested.load() || failed.load()) {
      write_checkpoint(checkpoint, meta, next);
      uint64_t completed = 0;
      for (int w = 0; w < WORKERS; ++w) completed += pairs_before(std::min(next[w].load(), vertices), w);
      const double elapsed = std::chrono::duration<double>(now - started).count();
      const double rate = elapsed ? completed / elapsed : 0;
      const double eta = rate ? (total_pairs - completed) / rate : 0;
      std::ostringstream msg;
      msg << "completed_pairs=" << completed << '/' << total_pairs << " percent="
          << std::fixed << std::setprecision(3) << (100.0 * completed / total_pairs)
          << " rate=" << std::setprecision(0) << rate << "/s elapsed=" << elapsed << "s eta=" << eta << 's';
      append_log(log_path, msg.str());
      std::cout << msg.str() << std::endl;
      last_report = now;
    }
  }
  for (auto& thread : threads) thread.join();
  write_checkpoint(checkpoint, meta, next);
  const double elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
  if (failed.load()) {
    const std::string msg = "COLLINEAR i=" + std::to_string(wi.load()) + " j=" + std::to_string(wj.load()) +
        " k=" + std::to_string(wk.load());
    append_log(log_path, msg);
    std::cerr << msg << std::endl;
    return 1;
  }
  if (stop_requested.load()) {
    append_log(log_path, "interrupted elapsed=" + std::to_string(elapsed) + "s");
    std::cout << "INTERRUPTED; checkpoint saved" << std::endl;
    return 130;
  }
  append_log(log_path, "VERIFIED vertices=" + std::to_string(vertices) + " pairs=" +
      std::to_string(total_pairs) + " elapsed=" + std::to_string(elapsed) + "s");
  std::cout << "EXHAUSTIVE VERIFIED vertices=" << vertices << " pairs=" << total_pairs
            << " no repeated vertex; no three collinear; elapsed=" << elapsed << "s" << std::endl;
  return 0;
} catch (const std::exception& e) {
  std::cerr << "ERROR: " << e.what() << std::endl;
  return 2;
}
