test:
	uv sync --reinstall
clean:
	rm .mypy_cache -r || true
	rm __pycache__ -r || true
	rm .ruff_cache -r || true
	rm module/_lib.so || true
	rm .zig-cache -r || true
