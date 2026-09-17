// Shared golden-vector reader for the DynaX Verilator testbenches.
//
// A deliberately small JSON scanner: the golden files are written by our own
// gen_golden.py with a fixed shape, so a dependency-free scan is enough and
// keeps every bench buildable inside the plain verilator container.
#pragma once

#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

namespace golden {

struct Case {
    std::string name;
    std::vector<long> input_ticks;
    std::vector<long> expected_value_ticks;
    std::vector<long> expected_idx;
};

inline std::string slurp(const char* path) {
    FILE* handle = std::fopen(path, "rb");
    if (!handle) { std::fprintf(stderr, "cannot open %s\n", path); std::exit(2); }
    std::string out;
    char buffer[65536];
    size_t got;
    while ((got = std::fread(buffer, 1, sizeof(buffer), handle)) > 0) out.append(buffer, got);
    std::fclose(handle);
    return out;
}

inline std::vector<long> numbers_after(const std::string& text, size_t& cursor, const char* key) {
    size_t at = text.find(key, cursor);
    if (at == std::string::npos) return {};
    size_t open = text.find('[', at);
    size_t close = text.find(']', open);
    std::vector<long> values;
    size_t i = open + 1;
    while (i < close) {
        while (i < close && (std::isspace((unsigned char)text[i]) || text[i] == ',')) i++;
        if (i >= close) break;
        char* end = nullptr;
        long value = std::strtol(text.c_str() + i, &end, 10);
        values.push_back(value);
        i = (size_t)(end - text.c_str());
    }
    cursor = close;
    return values;
}

inline std::vector<Case> load_cases(const char* path) {
    std::string text = slurp(path);
    std::vector<Case> cases;
    size_t cursor = 0;
    while (true) {
        size_t name_at = text.find("\"name\"", cursor);
        if (name_at == std::string::npos) break;
        size_t quote = text.find('"', text.find(':', name_at) + 1);
        size_t quote_end = text.find('"', quote + 1);
        Case item;
        item.name = text.substr(quote + 1, quote_end - quote - 1);
        cursor = quote_end;
        item.input_ticks = numbers_after(text, cursor, "\"input_ticks\"");
        item.expected_value_ticks = numbers_after(text, cursor, "\"expected_value_ticks\"");
        item.expected_idx = numbers_after(text, cursor, "\"expected_idx\"");
        if (item.input_ticks.empty()) break;
        cases.push_back(std::move(item));
    }
    return cases;
}

}  // namespace golden
