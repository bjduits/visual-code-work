# Workspace

This workspace operates using a 3-layer architecture to maximize reliability and consistency.

## Structure

- **`directives/`** - Standard Operating Procedures (SOPs) in Markdown defining what to do
- **`execution/`** - Deterministic Python scripts that do the work
- **`.env`** - Environment variables (API keys, tokens, etc.)
- **`CLAUD.md`** - Core operating principles and architecture

## Quick Start

1. Add directives to `directives/` folder following the template
2. Create corresponding execution scripts in `execution/` folder
3. Store secrets in `.env`
4. I'll orchestrate the work by reading directives and calling scripts appropriately

## Principles

- **Check for tools first** - Before writing anything, check if execution scripts exist
- **Self-anneal** - When things break, fix them, test, and update directives
- **Update as learned** - Directives evolve as we discover constraints and better approaches
