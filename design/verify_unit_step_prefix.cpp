// Exact, single-core all-triples test for a cyclic substitution prefix.
// Build with: g++ -O2 -std=c++17 -DSOURCE_SHA=\"$(sha256sum "$source" | cut -d' ' -f1)\" "$source" -o "$binary"
// Repeating the same command resumes completed anchors. SIGINT/SIGTERM flush a
// checkpoint; only the unfinished anchor is repeated. State/logs are separate
// from the final result. A finite clean prefix is NOT an infinite theorem.
#include <array>
#include <chrono>
#include <csignal>
#include <cstdint>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
#include <fcntl.h>
#include <unistd.h>

#ifndef SOURCE_SHA
#error Build with -DSOURCE_SHA set to the SHA256 of this source.
#endif
namespace fs = std::filesystem;
using Vec = std::array<int32_t, 8>;
volatile std::sig_atomic_t stopped = 0;
void stop(int) { stopped = 1; }
struct Hash {
    size_t operator()(const Vec& v) const {
        uint64_t h = 1469598103934665603ULL;
        for (auto x : v) { h ^= uint32_t(x); h *= 1099511628211ULL; }
        return h;
    }
};
std::string stamp() {
    auto t = std::time(nullptr);
    char out[32]; std::strftime(out, sizeof(out), "%Y-%m-%dT%H:%M:%SZ", std::gmtime(&t));
    return out;
}
void durable_write(const fs::path& path, const std::string& data, bool append = false) {
    fs::create_directories(path.parent_path().empty() ? "." : path.parent_path());
    auto target = append ? path : fs::path(path.string() + ".tmp");
    int fd = ::open(target.c_str(), O_WRONLY | O_CREAT | (append ? O_APPEND : O_TRUNC), 0600);
    if (fd < 0) throw std::runtime_error("cannot open " + target.string());
    size_t written = 0;
    while (written < data.size()) {
        auto n = ::write(fd, data.data() + written, data.size() - written);
        if (n <= 0) { ::close(fd); throw std::runtime_error("write failed"); }
        written += size_t(n);
    }
    if (::fsync(fd) != 0) { ::close(fd); throw std::runtime_error("fsync failed"); }
    ::close(fd);
    if (!append) fs::rename(target, path);
}
std::string array_json(const Vec& v, int k) {
    std::string s = "[";
    for (int j = 0; j < k; ++j) s += (j ? "," : "") + std::to_string(v[j]);
    return s + "]";
}
int main(int argc, char** argv) {
    fs::path dir = ".checkpoint-shallit-five", output = "results/shallit-five-prefix.json";
    std::string image = "01213101314310";
    int count = 38416, k = 5;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--help") {
            std::cout << "Exact all-triples cyclic substitution prefix check, one core.\n"
                      << "--steps N (default 38416, max 2000000) --alphabet K (2..8)\n"
                      << "--image0 WORD (starts in 0) --state-dir DIR --output FILE\n"
                      << "Automatically resumes a compatible checkpoint; interruption repeats only\n"
                      << "the unfinished anchor. JSONL progress every five seconds. Finite evidence only.\n";
            return 0;
        }
        if (++i == argc) throw std::runtime_error("missing argument value");
        if (arg == "--steps") count = std::stoi(argv[i]);
        else if (arg == "--alphabet") k = std::stoi(argv[i]);
        else if (arg == "--image0") image = argv[i];
        else if (arg == "--state-dir") dir = argv[i];
        else if (arg == "--output") output = argv[i];
        else throw std::runtime_error("unknown option " + arg);
    }
    if (count < 2 || count > 2000000 || k < 2 || k > 8 || image.size() < 2 || image[0] != '0')
        throw std::runtime_error("invalid bounded parameters");
    for (auto c : image) if (c < '0' || c >= '0' + k) throw std::runtime_error("invalid image letter");
    const std::string identity = std::string("v1|") + SOURCE_SHA + "|" + std::to_string(k) + "|" + std::to_string(count) + "|" + image;
    fs::create_directories(dir);
    auto checkpoint = dir / "checkpoint.txt", log = dir / "run.jsonl";
    auto event = [&](const std::string& type, const std::string& fields) {
        auto line = "{\"timestamp\":\"" + stamp() + "\",\"event\":\"" + type + "\"" + fields + "}\n";
        durable_write(log, line, true); std::cerr << line << std::flush;
    };
    int next = 0;
    auto completed_chords = [&](int n) -> uint64_t { return uint64_t(n) * (2ULL * count - n + 1) / 2; };
    auto save = [&]() {
        durable_write(checkpoint, identity + "\n" + std::to_string(next) + "\n" + std::to_string(completed_chords(next)) + "\n");
    };
    try {
        if (fs::exists(checkpoint)) {
            std::ifstream in(checkpoint);
            std::string saved; uint64_t chords = 0;
            std::getline(in, saved); in >> next >> chords;
            if (!in || saved != identity || next < 0 || next > count || chords != completed_chords(next))
                throw std::runtime_error("incompatible/corrupt checkpoint; use a different state directory");
        }
        event(next ? "resume" : "start", ",\"identity\":\"" + identity + "\",\"completed_anchors\":" + std::to_string(next)
              + ",\"total_anchors\":" + std::to_string(count) + ",\"threads\":1,\"checkpoint\":\"" + checkpoint.string() + "\"");
        std::signal(SIGINT, stop); std::signal(SIGTERM, stop);
        std::vector<uint8_t> word{0};
        while (word.size() < size_t(count)) {
            std::vector<uint8_t> expanded;
            expanded.reserve(std::min(size_t(count), word.size() * image.size()));
            for (auto c : word) {
                for (auto x : image) {
                    if (expanded.size() == size_t(count)) break;
                    expanded.push_back((c + x - '0') % k);
                }
                if (expanded.size() == size_t(count)) break;
            }
            word.swap(expanded);
        }
        std::vector<Vec> points(count + 1);
        for (int n = 0; n < count; ++n) { points[n+1] = points[n]; ++points[n+1][word[n]]; }
        auto start = std::chrono::steady_clock::now(), last = start;
        uint64_t initial = completed_chords(next), total = completed_chords(count);
        const std::string meta = "\"code_sha256\":\"" + std::string(SOURCE_SHA) + "\",\"alphabet\":" + std::to_string(k)
                              + ",\"steps\":" + std::to_string(count) + ",\"image0\":\"" + image + "\"";
        std::unordered_map<Vec, int, Hash> directions;
        directions.reserve(size_t(count) * 2);
        while (next < count) {
            directions.clear();
            for (int c = next + 1; c <= count; ++c) {
                if (stopped) { save(); event("interrupted", ",\"next_anchor\":" + std::to_string(next)); return 130; }
                Vec v{}; int d = 0;
                for (int j = 0; j < k; ++j) { v[j] = points[c][j] - points[next][j]; d = std::gcd(d, v[j]); }
                for (int j = 0; j < k; ++j) v[j] /= d;
                auto [it, fresh] = directions.emplace(v, c);
                if (!fresh) {
                    int b = it->second; Vec left{}, right{};
                    for (int j = 0; j < k; ++j) {
                        left[j] = points[b][j] - points[next][j]; right[j] = points[c][j] - points[b][j];
                        if (int64_t(c - b) * left[j] != int64_t(b - next) * right[j]) throw std::runtime_error("invalid witness");
                    }
                    durable_write(output, "{" + meta + ",\"status\":\"counterexample\",\"indices\":[" + std::to_string(next) + ","
                                  + std::to_string(b) + "," + std::to_string(c) + "],\"left_counts\":" + array_json(left, k)
                                  + ",\"right_counts\":" + array_json(right, k) + "}\n");
                    save(); event("counterexample", ",\"output\":\"" + output.string() + "\""); return 1;
                }
            }
            ++next;
            auto current = std::chrono::steady_clock::now();
            if (std::chrono::duration<double>(current - last).count() >= 5 || next == count) {
                save();
                double elapsed = std::chrono::duration<double>(current - start).count();
                double rate = (completed_chords(next) - initial) / std::max(elapsed, 1e-9);
                event("progress", ",\"completed_anchors\":" + std::to_string(next) + ",\"total_anchors\":" + std::to_string(count)
                      + ",\"completed_chords\":" + std::to_string(completed_chords(next)) + ",\"total_chords\":" + std::to_string(total)
                      + ",\"elapsed_seconds\":" + std::to_string(elapsed) + ",\"chords_per_second\":" + std::to_string(rate)
                      + ",\"eta_seconds\":" + std::to_string((total - completed_chords(next)) / std::max(rate, 1e-9)));
                last = current;
            }
        }
        durable_write(output, "{" + meta + ",\"status\":\"finite_prefix_pass\",\"vertices\":" + std::to_string(count + 1)
                      + ",\"chords_checked\":" + std::to_string(total) + ",\"scope\":\"All triples in this prefix only; not an infinite proof.\"}\n");
        event("complete", ",\"output\":\"" + output.string() + "\"");
    } catch (const std::exception& exc) {
        event("error", ",\"message\":\"" + std::string(exc.what()) + "\"");
        return 2;
    }
}
