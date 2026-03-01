from nodriver import *
async def cursor_illustration_show_native(tab):
    await tab.send(cdp.runtime.evaluate(expression="""
            function enableCursor() {
            var seleniumFollowerImg = document.createElement("img");
            seleniumFollowerImg.setAttribute('src', 'data:image/png;base64,'
                + 'iVBORw0KGgoAAAANSUhEUgAAABQAAAAeCAQAAACGG/bgAAAAAmJLR0QA/4ePzL8AAAAJcEhZcwAA'
                + 'HsYAAB7GAZEt8iwAAAAHdElNRQfgAwgMIwdxU/i7AAABZklEQVQ4y43TsU4UURSH8W+XmYwkS2I0'
                + '9CRKpKGhsvIJjG9giQmliHFZlkUIGnEF7KTiCagpsYHWhoTQaiUUxLixYZb5KAAZZhbunu7O/PKf'
                + 'e+fcA+/pqwb4DuximEqXhT4iI8dMpBWEsWsuGYdpZFttiLSSgTvhZ1W/SvfO1CvYdV1kPghV68a3'
                + '0zzUWZH5pBqEui7dnqlFmLoq0gxC1XfGZdoLal2kea8ahLoqKXNAJQBT2yJzwUTVt0bS6ANqy1ga'
                + 'VCEq/oVTtjji4hQVhhnlYBH4WIJV9vlkXLm+10R8oJb79Jl1j9UdazJRGpkrmNkSF9SOz2T71s7M'
                + 'SIfD2lmmfjGSRz3hK8l4w1P+bah/HJLN0sys2JSMZQB+jKo6KSc8vLlLn5ikzF4268Wg2+pPOWW6'
                + 'ONcpr3PrXy9VfS473M/D7H+TLmrqsXtOGctvxvMv2oVNP+Av0uHbzbxyJaywyUjx8TlnPY2YxqkD'
                + 'dAAAAABJRU5ErkJggg==');
            seleniumFollowerImg.setAttribute('id', 'selenium_mouse_follower');
            seleniumFollowerImg.setAttribute('style', 'position: absolute; z-index: 99999999999; pointer-events: none; width: 20px; height: 32px; left:-100px; top:-100px');
            document.body.appendChild(seleniumFollowerImg);
            document.onmousemove = function (e) {
                document.getElementById("selenium_mouse_follower").style.left = e.pageX + 'px';
                document.getElementById("selenium_mouse_follower").style.top = e.pageY + 'px';
            };
            };

            enableCursor();"""))

async def cursor_illustration_delete_native(tab):
    await tab.send(cdp.runtime.evaluate(expression="""function deleteCursor(){const imgElement = document.getElementById('selenium_mouse_follower');
                                        if (imgElement) {imgElement.remove();
                                        } else {
                                        console.warn('No element found with id "selenium_mouse_follower".');
                                        };};
                                        deleteCursor();
                                        """))