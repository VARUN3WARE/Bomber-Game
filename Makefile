# Compiler and flags
CXX = g++
CXXFLAGS = -std=c++17 -Iinclude -Wall -g

# Directories
SRCDIR = src
INCDIR = include
BUILDDIR = build
TARGET = bomberman

# Source files and object files
SRCS = $(wildcard $(SRCDIR)/*.cpp)
OBJS = $(patsubst $(SRCDIR)/%.cpp, $(BUILDDIR)/%.o, $(SRCS))

# Default target
all: $(TARGET)

# Link the executable
$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJS)

# Compile source files to object files
$(BUILDDIR)/%.o: $(SRCDIR)/%.cpp
	@mkdir -p $(BUILDDIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean up build files
clean:
	rm -rf $(BUILDDIR) $(TARGET)

# Phony targets
.PHONY: all clean
