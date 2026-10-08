# Bug fixes

## Node app (`nodejs/`)
| # | File | Bug | Fix |
|---|------|-----|-----|
| 1 | `src/routes/books.js` | `GET /search` declared after `GET /:id`, so "search" was treated as an id (404) | Moved `/search` above `/:id` |
| 2 | `src/repositories/bookRepository.js` | Category filter used `category != ?` (returned every *other* category) | Changed to `category = ?` |
| 3 | `src/services/bookService.js` | `updateBook` parameters were `(…, publishedYear, price, …)` but the controller passes `(…, price, published_year, …)`, swapping price and year on every edit | Reordered the parameters to match |
| 4 | `src/services/stockService.js` | Negative adjustment added `abs(delta)`, so the "-" button increased stock and the "Insufficient stock" check never fired | Always `quantity + delta` |
| 5 | `src/repositories/statsRepository.js` | `available_copies` ignored books with quantity 1 (`quantity > 1`) | `SUM(quantity)` |
| 6 | `frontend/js/app.js` | Search used the *previous* keystroke's value (`pendingQuery`), so results lagged one character behind; responses could also arrive out of order | Search the current value, debounced, ignore stale responses |
| 7 | `frontend/js/app.js`, `index.html` | Save errors (e.g. duplicate ISBN) were written to a message behind the modal dialog, so users never saw them | Added an error line inside the dialog |
| 8 | `frontend/css/styles.css` | Fixed `hidden` attribute being overridden by `display` rules | Added `[hidden]{display:none!important}` |
| 9 | `src/server.js` | No startup message | Logs the URL |

## Python app (`python/`)
| # | File | Bug | Fix |
|---|------|-----|-----|
| 1 | `app/services/pipeline.py` | `prepare_for_ocr(preprocessed, resized)` had arguments swapped, so OCR ran on the unprocessed colour image | Correct argument order |
| 2 | `app/preprocessing/image_ops.py` | `resize_image` forced every image to 800x600, distorting aspect ratio (tall/wide notes) and upscaling small ones | Aspect-preserving downscale only |
| 3 | `app/preprocessing/image_ops.py` | `THRESH_BINARY_INV` produced white text on black; Tesseract expects dark text on light | `THRESH_BINARY` |
| 4 | `app/recognition/ocr.py` | `--psm 7` reads a single line only, dropping multi-line notes | `--psm 6` (block of text) |
| 5 | `app/utils/files.py` | `read_result` opened the file with `"w+"`, truncating it, so downloads were always empty | Open with `"r"` |
| 6 | `app/routes/recognize.py` | Missing Tesseract caused an unhandled 500 traceback | Returns a clear JSON error |
| 7 | `frontend/static/js/app.js` | Network/non-JSON failures left the button disabled; object URLs leaked | try/catch, revoke old URL |
| 8 | `frontend/static/css/styles.css` | `.preview{display:block}` overrode `hidden`, showing empty broken images | `[hidden]{display:none!important}` |

Regression tests were added for each backend fix (Node: 18 tests, Python: 12 tests).
