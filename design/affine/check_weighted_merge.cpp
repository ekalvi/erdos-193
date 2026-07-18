#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <unordered_map>
#include <vector>

// Exact checker for the dimension-correct candidate
//
//   R_n(C) = W_n + C W_{2n} + C^2 W_{5n} in Z^3.
//
// W is the projected fixed point of Lidbetter's 12-symbol, seven-uniform
// morphism.  Every R-step has coordinate sum 1+2C+5C^2, which is positive
// for every integer C.  Hence, from a fixed first vertex, two later vertices
// form a collinear triple exactly when their primitive chord directions agree.
// The program checks every such chord with exact integer arithmetic.

namespace {

using BasePoint = std::array<int, 3>;
using Point = std::array<long long, 3>;

struct Key {
  long long x;
  long long y;
  long long z;

  bool operator==(const Key& other) const {
    return x == other.x && y == other.y && z == other.z;
  }
};

std::uint64_t mix(std::uint64_t x) {
  x ^= x >> 30;
  x *= 0xbf58476d1ce4e5b9ULL;
  x ^= x >> 27;
  x *= 0x94d049bb133111ebULL;
  return x ^ (x >> 31);
}

struct Hash {
  std::size_t operator()(const Key& key) const {
    const auto x = mix(static_cast<std::uint64_t>(key.x));
    const auto y = mix(static_cast<std::uint64_t>(key.y));
    const auto z = mix(static_cast<std::uint64_t>(key.z));
    return static_cast<std::size_t>(x ^ (y << 1) ^ (z << 7));
  }
};

constexpr int kMorphism[12][7] = {
    {0, 4, 9, 0, 8, 9, 0},       {1, 5, 10, 1, 6, 10, 1},
    {2, 3, 11, 2, 7, 11, 2},     {3, 2, 6, 3, 10, 6, 3},
    {4, 0, 7, 4, 11, 7, 4},      {5, 1, 8, 5, 9, 8, 5},
    {6, 3, 2, 6, 3, 10, 6},      {7, 4, 0, 7, 4, 11, 7},
    {8, 5, 1, 8, 5, 9, 8},       {9, 0, 4, 9, 0, 8, 9},
    {10, 1, 5, 10, 1, 6, 10},    {11, 2, 3, 11, 2, 7, 11},
};

struct Options {
  int limit = 10000;
  int coefficient = 3;
};

long parse_long(const char* text, const char* label) {
  char* end = nullptr;
  const long value = std::strtol(text, &end, 10);
  if (end == text || *end != '\0') {
    throw std::runtime_error(std::string("invalid ") + label);
  }
  return value;
}

Options parse_options(int argc, char** argv) {
  if (argc > 3) {
    throw std::runtime_error(
        "usage: check_weighted_merge [largest-index] [coefficient]");
  }
  Options options;
  if (argc >= 2) {
    const long value = parse_long(argv[1], "largest-index");
    if (value < 2 || value > 2000000L) {
      throw std::runtime_error("largest-index must lie in [2,2000000]");
    }
    options.limit = static_cast<int>(value);
  }
  if (argc == 3) {
    const long value = parse_long(argv[2], "coefficient");
    if (value < -1000 || value > 1000) {
      throw std::runtime_error("coefficient must lie in [-1000,1000]");
    }
    options.coefficient = static_cast<int>(value);
  }
  return options;
}

long long absolute(long long value) { return value < 0 ? -value : value; }

Key primitive_direction(const Point& a, const Point& b) {
  const long long x = b[0] - a[0];
  const long long y = b[1] - a[1];
  const long long z = b[2] - a[2];
  const long long divisor =
      std::gcd(absolute(x), std::gcd(absolute(y), absolute(z)));
  if (divisor == 0) {
    throw std::runtime_error("repeated vertex");
  }
  return {x / divisor, y / divisor, z / divisor};
}

void print_point(const Point& point) {
  std::cout << '[' << point[0] << ',' << point[1] << ',' << point[2] << ']';
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const Options options = parse_options(argc, argv);
    const int limit = options.limit;
    const long long coefficient = options.coefficient;
    const long long coefficient_squared = coefficient * coefficient;
    const long long height =
        1 + 2 * coefficient + 5 * coefficient_squared;
    if (height <= 0) {
      throw std::runtime_error("internal error: nonpositive step height");
    }

    std::vector<unsigned char> symbols;
    symbols.reserve(static_cast<std::size_t>(5) * limit + 7);
    for (std::size_t q = 0;
         symbols.size() < static_cast<std::size_t>(5) * limit + 1; ++q) {
      const int current = q == 0 ? 0 : symbols.at(q);
      for (int r = 0; r < 7; ++r) {
        symbols.push_back(static_cast<unsigned char>(kMorphism[current][r]));
      }
    }
    symbols.resize(static_cast<std::size_t>(5) * limit + 1);

    std::vector<BasePoint> walk(symbols.size() + 1);
    for (std::size_t i = 0; i < symbols.size(); ++i) {
      walk[i + 1] = walk[i];
      ++walk[i + 1][symbols[i] % 3];
    }

    std::vector<Point> merged(static_cast<std::size_t>(limit) + 1);
    for (int n = 0; n <= limit; ++n) {
      for (int coordinate = 0; coordinate < 3; ++coordinate) {
        merged[n][coordinate] =
            static_cast<long long>(walk[n][coordinate]) +
            coefficient * walk[2 * n][coordinate] +
            coefficient_squared * walk[5 * n][coordinate];
      }
    }

    std::uint64_t chords_checked = 0;
    for (int i = 0; i <= limit - 2; ++i) {
      std::unordered_map<Key, int, Hash> first_on_direction;
      first_on_direction.reserve(static_cast<std::size_t>(limit - i) * 2);
      for (int j = i + 1; j <= limit; ++j) {
        ++chords_checked;
        const Key key = primitive_direction(merged[i], merged[j]);
        const auto [where, inserted] = first_on_direction.emplace(key, j);
        if (!inserted) {
          const int middle = where->second;
          std::cout << "{\"status\":\"counterexample\",\"largest_index\":"
                    << limit << ",\"coefficient\":" << coefficient
                    << ",\"step_height\":" << height << ",\"indices\":["
                    << i << ',' << middle << ',' << j << "],\"points\":[";
          print_point(merged[i]);
          std::cout << ',';
          print_point(merged[middle]);
          std::cout << ',';
          print_point(merged[j]);
          std::cout << "],\"primitive_direction\":[" << key.x << ',' << key.y
                    << ',' << key.z << "],\"chords_checked\":"
                    << chords_checked << "}\n";
          return 1;
        }
      }
      if (i % 1000 == 0) {
        std::cerr << "i=" << i << " chords=" << chords_checked << '\n';
      }
    }

    std::cout << "{\"status\":\"no-counterexample-in-prefix\","
              << "\"largest_index\":" << limit << ",\"vertices\":"
              << limit + 1 << ",\"coefficient\":" << coefficient
              << ",\"step_height\":" << height << ",\"chords_checked\":"
              << chords_checked << "}\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
}
