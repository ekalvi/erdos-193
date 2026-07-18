#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <unordered_map>
#include <vector>

// Exact prefix checker for P_n = (W_n, W_{2n}, W_{5n}) in Z^9.
//
// W is the three-coordinate walk obtained by projecting Lidbetter's
// twelve-symbol, seven-uniform fixed point modulo three.  The program hashes
// every primitive W-chord direction from a fixed first index.  Only triples
// collinear in that first projection can be collinear in P; those triples are
// checked in the 2n and 5n projections with exact integer determinants.

namespace {

using Point = std::array<int, 3>;

struct Key {
  int x;
  int y;
  int z;
  bool operator==(const Key& other) const {
    return x == other.x && y == other.y && z == other.z;
  }
};

struct Hash {
  std::size_t operator()(const Key& key) const {
    std::uint64_t h = static_cast<std::uint32_t>(key.x) * 0x9e3779b1u;
    h ^= static_cast<std::uint32_t>(key.y) + 0x9e3779b97f4a7c15ULL +
         (h << 6) + (h >> 2);
    h ^= static_cast<std::uint32_t>(key.z) + 0x9e3779b97f4a7c15ULL +
         (h << 6) + (h >> 2);
    return static_cast<std::size_t>(h);
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

int parse_limit(int argc, char** argv) {
  if (argc > 2) {
    throw std::runtime_error("usage: check_affine_125 [largest-index]");
  }
  const long value = argc == 2 ? std::strtol(argv[1], nullptr, 10) : 10000;
  if (value < 2 || value > 100000000L) {
    throw std::runtime_error("largest-index must lie in [2,100000000]");
  }
  return static_cast<int>(value);
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const int limit = parse_limit(argc, argv);

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

    std::vector<Point> walk(symbols.size() + 1);
    for (std::size_t i = 0; i < symbols.size(); ++i) {
      walk[i + 1] = walk[i];
      ++walk[i + 1][symbols[i] % 3];
    }

    long long base_triples = 0;
    long long minimum_raw = (1LL << 60);
    long long minimum_i = 0;
    long long minimum_mid = 0;
    long long minimum_j = 0;
    long double minimum_normalized = 1e100L;
    long long normalized_i = 0;
    long long normalized_mid = 0;
    long long normalized_j = 0;
    long long normalized_raw = 0;
    long double minimum_scale_normalized = 1e100L;
    long long scale_i = 0;
    long long scale_mid = 0;
    long long scale_j = 0;
    long long scale_raw = 0;
    int scale_exponent = 0;
    std::array<long long, 17> modular_survivors{};

    for (int i = 0; i <= limit - 2; ++i) {
      std::unordered_map<Key, std::vector<int>, Hash> buckets;
      buckets.reserve(static_cast<std::size_t>(limit - i) * 2);
      for (int j = i + 1; j <= limit; ++j) {
        const int x = walk[j][0] - walk[i][0];
        const int y = walk[j][1] - walk[i][1];
        const int z = walk[j][2] - walk[i][2];
        const int divisor = std::gcd(x, std::gcd(y, z));
        const Key key{x / divisor, y / divisor, z / divisor};
        auto& prior = buckets[key];

        for (const int mid : prior) {
          ++base_triples;
          bool zero = true;
          long long raw = 0;
          std::array<long long, 6> defects{};
          int defect_count = 0;
          for (const int multiplier : {2, 5}) {
            for (int coordinate = 0; coordinate < 3; ++coordinate) {
              const long long first =
                  walk[multiplier * mid][coordinate] -
                  walk[multiplier * i][coordinate];
              const long long second =
                  walk[multiplier * j][coordinate] -
                  walk[multiplier * mid][coordinate];
              const long long defect =
                  static_cast<long long>(j - mid) * first -
                  static_cast<long long>(mid - i) * second;
              defects[defect_count++] = defect;
              raw = std::max(raw, std::llabs(defect));
              zero = zero && defect == 0;
            }
          }

          for (int modulus = 2; modulus <= 16; ++modulus) {
            bool modular_zero = true;
            for (const long long defect : defects) {
              modular_zero = modular_zero && defect % modulus == 0;
            }
            modular_survivors[modulus] += modular_zero;
          }

          if (raw < minimum_raw) {
            minimum_raw = raw;
            minimum_i = i;
            minimum_mid = mid;
            minimum_j = j;
          }
          const long double normalized =
              static_cast<long double>(raw) /
              (static_cast<long double>(mid - i) * (j - mid));
          if (normalized < minimum_normalized) {
            minimum_normalized = normalized;
            normalized_i = i;
            normalized_mid = mid;
            normalized_j = j;
            normalized_raw = raw;
          }
          const int maximum_gap = std::max(mid - i, j - mid);
          int exponent = 0;
          int gap_scale = 1;
          long long defect_scale = 1;
          while (gap_scale <= maximum_gap / 7) {
            gap_scale *= 7;
            defect_scale *= 28;
            ++exponent;
          }
          const long double scale_normalized =
              static_cast<long double>(raw) / defect_scale;
          if (scale_normalized < minimum_scale_normalized) {
            minimum_scale_normalized = scale_normalized;
            scale_i = i;
            scale_mid = mid;
            scale_j = j;
            scale_raw = raw;
            scale_exponent = exponent;
          }

          if (zero) {
            std::cout << "{\"status\":\"counterexample\",\"largest_index\":"
                      << limit << ",\"indices\":[" << i << ',' << mid << ','
                      << j << "],\"base_projection_triples_checked\":"
                      << base_triples << "}\n";
            return 1;
          }
        }
        prior.push_back(j);
      }
      if (i % 1000 == 0) {
        std::cerr << "i=" << i << " base_triples=" << base_triples << '\n';
      }
    }

    std::cout << "{\"status\":\"no-counterexample-in-prefix\","
              << "\"largest_index\":" << limit << ','
              << "\"vertices\":" << limit + 1 << ','
              << "\"base_projection_triples_checked\":" << base_triples << ','
              << "\"minimum_raw_defect\":" << minimum_raw << ','
              << "\"minimum_raw_indices\":[" << minimum_i << ',' << minimum_mid
              << ',' << minimum_j << "],"
              << "\"minimum_normalized_defect\":"
              << static_cast<double>(minimum_normalized) << ','
              << "\"minimum_normalized_raw\":" << normalized_raw << ','
              << "\"minimum_normalized_indices\":[" << normalized_i << ','
              << normalized_mid << ',' << normalized_j << "],"
              << "\"minimum_scale_normalized_defect\":"
              << static_cast<double>(minimum_scale_normalized) << ','
              << "\"minimum_scale_normalized_raw\":" << scale_raw << ','
              << "\"minimum_scale_exponent\":" << scale_exponent << ','
              << "\"minimum_scale_normalized_indices\":[" << scale_i << ','
              << scale_mid << ',' << scale_j << "],"
              << "\"modular_survivors\":{";
    for (int modulus = 2; modulus <= 16; ++modulus) {
      if (modulus != 2) std::cout << ',';
      std::cout << '\"' << modulus << "\":" << modular_survivors[modulus];
    }
    std::cout << "}}\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
}
