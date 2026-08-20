#ifndef COSC7502_LIFE_H
#define COSC7502_LIFE_H

#include <cstddef>
#include <cstdint>
#include <vector>

class Life {
public:
    using Cell = std::uint8_t;

    Life(std::size_t width, std::size_t height);

    std::size_t width() const noexcept;
    std::size_t height() const noexcept;

    void clear() noexcept;
    void randomise(double density_percent, std::uint32_t seed);
    void set(std::size_t x, std::size_t y, bool alive);
    bool alive(std::size_t x, std::size_t y) const;

    void step();
    void run(std::size_t generations);

    std::uint64_t live_count() const noexcept;
    std::uint64_t checksum() const noexcept;

private:
    using Grid = std::vector<std::vector<Cell>>;

    static std::size_t wrap(long long coordinate, std::size_t extent) noexcept;
    unsigned live_neighbours(std::size_t x, std::size_t y) const noexcept;

    std::size_t width_;
    std::size_t height_;
    Grid current_;
    Grid next_;
};

#endif
