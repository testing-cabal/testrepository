// Populate the sidebar
//
// This is a script, and not included directly in the page, to control the total size of the book.
// The TOC contains an entry for each page, so if each page includes a copy of the TOC,
// the total size of the page becomes O(n**2).
class MDBookSidebarScrollbox extends HTMLElement {
    constructor() {
        super();
    }
    connectedCallback() {
        this.innerHTML = '<ol class="chapter"><li class="chapter-item expanded affix "><a href="overview.html">Overview</a></li><li class="chapter-item expanded affix "><li class="part-title">Manual</li><li class="chapter-item expanded "><a href="configuration.html"><strong aria-hidden="true">1.</strong> Configuration</a></li><li class="chapter-item expanded "><a href="running-tests.html"><strong aria-hidden="true">2.</strong> Running tests</a></li><li class="chapter-item expanded "><a href="listing-tests.html"><strong aria-hidden="true">3.</strong> Listing tests</a></li><li class="chapter-item expanded "><a href="parallel-testing.html"><strong aria-hidden="true">4.</strong> Parallel testing</a></li><li class="chapter-item expanded "><a href="grouping-tests.html"><strong aria-hidden="true">5.</strong> Grouping tests</a></li><li class="chapter-item expanded "><a href="remote-or-isolated-test-environments.html"><strong aria-hidden="true">6.</strong> Remote or isolated test environments</a></li><li class="chapter-item expanded "><a href="hiding-tests.html"><strong aria-hidden="true">7.</strong> Hiding tests</a></li><li class="chapter-item expanded "><a href="automated-test-isolation-bisection.html"><strong aria-hidden="true">8.</strong> Automated test isolation bisection</a></li><li class="chapter-item expanded "><a href="forcing-isolation.html"><strong aria-hidden="true">9.</strong> Forcing isolation</a></li><li class="chapter-item expanded "><a href="repositories.html"><strong aria-hidden="true">10.</strong> Repositories</a></li><li class="chapter-item expanded "><a href="setuptools-integration.html"><strong aria-hidden="true">11.</strong> Setuptools integration</a></li><li class="chapter-item expanded affix "><li class="part-title">Developers</li><li class="chapter-item expanded "><a href="developers/development-guidelines.html"><strong aria-hidden="true">12.</strong> Development guidelines</a></li><li class="chapter-item expanded affix "><li class="part-title">Design</li><li class="chapter-item expanded "><a href="design/design.html"><strong aria-hidden="true">13.</strong> Design</a></li></ol>';
        // Set the current, active page, and reveal it if it's hidden
        let current_page = document.location.href.toString().split("#")[0];
        if (current_page.endsWith("/")) {
            current_page += "index.html";
        }
        var links = Array.prototype.slice.call(this.querySelectorAll("a"));
        var l = links.length;
        for (var i = 0; i < l; ++i) {
            var link = links[i];
            var href = link.getAttribute("href");
            if (href && !href.startsWith("#") && !/^(?:[a-z+]+:)?\/\//.test(href)) {
                link.href = path_to_root + href;
            }
            // The "index" page is supposed to alias the first chapter in the book.
            if (link.href === current_page || (i === 0 && path_to_root === "" && current_page.endsWith("/index.html"))) {
                link.classList.add("active");
                var parent = link.parentElement;
                if (parent && parent.classList.contains("chapter-item")) {
                    parent.classList.add("expanded");
                }
                while (parent) {
                    if (parent.tagName === "LI" && parent.previousElementSibling) {
                        if (parent.previousElementSibling.classList.contains("chapter-item")) {
                            parent.previousElementSibling.classList.add("expanded");
                        }
                    }
                    parent = parent.parentElement;
                }
            }
        }
        // Track and set sidebar scroll position
        this.addEventListener('click', function(e) {
            if (e.target.tagName === 'A') {
                sessionStorage.setItem('sidebar-scroll', this.scrollTop);
            }
        }, { passive: true });
        var sidebarScrollTop = sessionStorage.getItem('sidebar-scroll');
        sessionStorage.removeItem('sidebar-scroll');
        if (sidebarScrollTop) {
            // preserve sidebar scroll position when navigating via links within sidebar
            this.scrollTop = sidebarScrollTop;
        } else {
            // scroll sidebar to current active section when navigating via "next/previous chapter" buttons
            var activeSection = document.querySelector('#sidebar .active');
            if (activeSection) {
                activeSection.scrollIntoView({ block: 'center' });
            }
        }
        // Toggle buttons
        var sidebarAnchorToggles = document.querySelectorAll('#sidebar a.toggle');
        function toggleSection(ev) {
            ev.currentTarget.parentElement.classList.toggle('expanded');
        }
        Array.from(sidebarAnchorToggles).forEach(function (el) {
            el.addEventListener('click', toggleSection);
        });
    }
}
window.customElements.define("mdbook-sidebar-scrollbox", MDBookSidebarScrollbox);
