# Design

## Values

Code reuse.
Focus on the project.
Do one thing well.

## Goals

Achieve a Clean UI, responsive UI, small-tools approach. Simultaneously have
a small clean code base which is easily approachable.

## Data model/storage

testrepository stores subunit streams as subunit streams in .testrespository
with simple additional metadata. See the [manual](../repositories.md) for documentation on the repository layout.
The key design elements are that streams are stored verbatim, and a testr managed stream called 'failing' is used  to track the current failures.

## Code layout

One conceptual thing per module, packages for anything where multiple types
are expected (e.g. testrepository.commands, testrespository.ui).

Generic driver code should not trigger lots of imports: code dependencies
should be loaded when needed. For example, argument validation uses argument
types that each command can import, so the core code doesn't need to know about
all types.

The tests for the code in testrepository.foo.bar is in
testrepository.tests.foo.test_bar. Interface tests for testrepository.foo is
in testrepository.tests.test_foo.

## External integration


Test Repository command, ui, parsing etc objects should all be suitable for
reuse from other programs.

## Threads/concurrency

In general using any public interface is fine, but keeping syncronisation
needs to a minimum for code readability.
