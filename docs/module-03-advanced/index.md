# Module 3: Advanced Validation

This module takes validation from basic consistency checking to a complete, extensible validation system.

**Total Time**: ~2 hours

## What You'll Build

A validation pipeline that:

- Validates numeric ranges (feedrate limits, diameter bounds)
- Checks naming conventions with regex
- Loads rules from configuration files
- Reports errors with rich context

## Tutorials

| # | Tutorial | Time | What You Build |
|---|----------|------|----------------|
| 09 | [Range & Regex Validation](09-range-regex-validation.md) | 40 min | Composable validators using Strategy pattern |
| 10 | [Validation Pipeline](10-validation-pipeline.md) | 35 min | Chain validators, aggregate errors |
| 11 | [Config-Driven Rules](11-config-driven-rules.md) | 45 min | Load validation rules from JSON/YAML |

## Engineering Concepts

This module focuses heavily on:

- **Strategy Pattern**: Swappable validation algorithms
- **Open/Closed Principle**: Add validators without modifying existing code
- **Configuration over Code**: Rules in data, not hardcoded
- **Error Aggregation**: Collecting vs failing on first error

## Prerequisites

Complete Module 2 (specifically Tutorial 08: Tool Consistency) before starting.
