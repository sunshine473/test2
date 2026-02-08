# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This repository is documentation-focused with no build pipeline. Use these commands for maintenance:

- **List files**: `ls -R` or `Get-ChildItem -Recurse`
- **Search content**: `grep -r "pattern" .` or `rg "pattern"`
- **Find TODOs**: `grep -r "TODO" .`

## Architecture & Structure

This project is a collection of reference materials for designing Claude Skills and Agents.

- **`参考/` (Reference)**: Contains core documentation, prompts, and guides for Claude Skills.
  - Includes guides like `How to create Skills for Claude` and role-specific prompts (e.g., `资深 Claude Skills 架构师 prompt.md`).
- **`AGENTS.md`**: Contributor guide and repository conventions.

## Style & Conventions

- **File Naming**: Use descriptive names. Prefer `kebab-case` or standard spacing for documentation files.
- **Content**:
  - Use clear section headings.
  - Use fenced code blocks for prompts and examples.
- **Security**: Never commit real API keys or secrets; use placeholders like `<API_KEY>`.
