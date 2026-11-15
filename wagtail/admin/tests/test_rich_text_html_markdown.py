from unittest.mock import patch

from django.core.files.base import ContentFile
from django.test import SimpleTestCase, TestCase

from wagtail import blocks
from wagtail.admin.rich_text.converters.html_markdown import (
    html_to_markdown,
)
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.contrib.typed_table_block.blocks import TypedTableBlock
from wagtail.documents.models import Document
from wagtail.embeds.models import Embed
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.rich_text import expand_db_html
from wagtail.test.utils import Page, PageFixturesMixin


class HTMLToMarkdownTestCase(SimpleTestCase):
    base_url = None

    def assertMarkdown(self, html, expected):
        self.assertEqual(html_to_markdown(html, base_url=self.base_url), expected)


class TestText(HTMLToMarkdownTestCase):
    def test_empty(self):
        self.assertMarkdown("", "")
        self.assertMarkdown("  \n\t ", "")
        self.assertMarkdown("<p>&nbsp;</p><p></p>", "")

    def test_bare_text(self):
        self.assertMarkdown("Just text", "Just text\n")

    def test_paragraphs(self):
        self.assertMarkdown("<p>One</p><p>Two</p>", "One\n\nTwo\n")

    def test_whitespace_collapsed(self):
        self.assertMarkdown("<p>  a \n\n  b\t c  </p>", "a b c\n")

    def test_entities(self):
        self.assertMarkdown(
            "<p>&lt;tag&gt; &amp; &copy; &quot;q&quot; &#x1F600;</p>",
            '\\<tag> & © "q" 😀\n',
        )

    def test_unicode(self):
        self.assertMarkdown("<p>שלום — 日本語 🎉</p>", "שלום — 日本語 🎉\n")

    def test_markdown_syntax_in_text_is_escaped(self):
        self.assertMarkdown(
            "<p>*star* _under_ snake_case [br] `tick`</p>"
            "<p># hash</p><p>1. one</p><p>- dash</p><p>&gt; gt</p>",
            "\\*star\\* \\_under\\_ snake_case \\[br\\] \\`tick\\`\n\n"
            "\\# hash\n\n1\\. one\n\n\\- dash\n\n\\> gt\n",
        )

    def test_html_in_text_is_escaped(self):
        self.assertMarkdown(
            "<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>",
            "\\<script>alert(1)\\</script>\n",
        )

    def test_line_breaks(self):
        self.assertMarkdown("<p>a<br>b<br/>c</p>", "a\\\nb\\\nc\n")

    def test_trailing_line_break_dropped(self):
        self.assertMarkdown("<p>a<br></p><p><em>b<br></em></p>", "a\n\n*b*\n")

    def test_redundant_line_breaks_dropped(self):
        self.assertMarkdown(
            "<p><br>a<br><br>b<a href='/x'><br>c</a><strong>d<br></strong>e</p>",
            "a\\\nb\\\n[c](/x)**d**\\\ne\n",
        )

    def test_top_level_line_breaks_ignored(self):
        self.assertMarkdown("<p>a</p><br><p>b</p>", "a\n\nb\n")

    def test_text_resembling_internal_tokens_kept(self):
        self.assertMarkdown(
            "<p>WAGTAILMDRAW0Z WAGTAILMDRAW7Z</p><pre>x</pre>",
            "WAGTAILMDRAW0Z WAGTAILMDRAW7Z\n\n```\nx\n```\n",
        )


class TestInlineStyles(HTMLToMarkdownTestCase):
    def test_bold_and_italic(self):
        self.assertMarkdown(
            "<p><strong>s</strong> <b>b</b> <em>e</em> <i>i</i></p>",
            "**s** **b** *e* *i*\n",
        )

    def test_nested_bold_italic(self):
        self.assertMarkdown("<p><strong><em>x</em></strong></p>", "***x***\n")

    def test_strikethrough_variants(self):
        self.assertMarkdown(
            "<p><s>s</s> <del>d</del> <strike>t</strike></p>", "~~s~~ ~~d~~ ~~t~~\n"
        )

    def test_code_variants(self):
        self.assertMarkdown(
            "<p><code>c</code> <kbd>k</kbd> <samp>s</samp> <var>v</var> <tt>t</tt></p>",
            "`c` `k` `s` `v` `t`\n",
        )

    def test_code_containing_backtick(self):
        self.assertMarkdown("<p><code>a`b</code></p>", "``a`b``\n")

    def test_superscript_and_subscript_kept_as_html(self):
        self.assertMarkdown(
            "<p>x<sup>2</sup> H<sub>2</sub>O</p>", "x<sup>2</sup> H<sub>2</sub>O\n"
        )

    def test_cite_and_dfn_become_italic(self):
        self.assertMarkdown("<p><cite>c</cite> <dfn>d</dfn></p>", "*c* *d*\n")

    def test_presentational_elements_unwrapped(self):
        self.assertMarkdown(
            "<p><u>u</u> <mark>m</mark> <small>s</small> <span>sp</span> "
            "<abbr title='x'>ab</abbr> <time>t</time> <font>f</font></p>",
            "u m s sp ab t f\n",
        )

    def test_inline_quote(self):
        self.assertMarkdown("<p><q>quoted</q></p>", "“quoted”\n")

    def test_whitespace_inside_styles_moved_outside(self):
        self.assertMarkdown(
            "<p><strong>bold </strong>next <em> it</em>x</p>", "**bold** next *it*x\n"
        )

    def test_intraword_emphasis(self):
        self.assertMarkdown(
            "<p>foo<strong>bar</strong>baz</p>",
            "foo**bar**baz\n",
        )

    def test_style_split_around_link(self):
        self.assertMarkdown(
            "<p><strong>bold <a href='/y'>link</a> more</strong></p>",
            "**bold** [**link**](/y) **more**\n",
        )

    def test_empty_styles_dropped(self):
        self.assertMarkdown("<p>a<strong></strong>b</p>", "ab\n")


class TestHeadings(HTMLToMarkdownTestCase):
    def test_all_levels(self):
        self.assertMarkdown(
            "".join(f"<h{i}>H{i}</h{i}>" for i in range(1, 7)),
            "# H1\n\n## H2\n\n### H3\n\n#### H4\n\n##### H5\n\n###### H6\n",
        )

    def test_inline_content(self):
        self.assertMarkdown(
            "<h2><a href='/x'>Linked</a> <code>c</code></h2>",
            "## [Linked](/x) `c`\n",
        )

    def test_line_break_in_heading(self):
        self.assertMarkdown("<h2>One<br>two</h2>", "## One two\n")

    def test_block_inside_heading(self):
        self.assertMarkdown("<h2><div>Div</div></h2>", "## Div\n")

    def test_code_block_inside_heading(self):
        self.assertMarkdown("<h2>a<pre>x</pre></h2>", "## a\n\n```\nx\n```\n")

    def test_uppercase_tags(self):
        self.assertMarkdown("<H2>Up</H2><P><STRONG>b</STRONG></P>", "## Up\n\n**b**\n")


class TestLinks(HTMLToMarkdownTestCase):
    base_url = "https://example.com/blog/"

    def test_absolute(self):
        self.assertMarkdown(
            "<p><a href='https://wagtail.org'>W</a></p>", "[W](https://wagtail.org)\n"
        )

    def test_relative_made_absolute(self):
        self.assertMarkdown(
            "<p><a href='/x/'>a</a> <a href='y/'>b</a> <a href='#top'>c</a> "
            "<a href='?q=1'>d</a> <a href='//cdn.example.org/z'>e</a></p>",
            "[a](https://example.com/x/) [b](https://example.com/blog/y/) "
            "[c](https://example.com/blog/#top) [d](https://example.com/blog/?q=1) "
            "[e](https://cdn.example.org/z)\n",
        )

    def test_relative_kept_without_base_url(self):
        self.assertEqual(html_to_markdown("<a href='/x/'>a</a>"), "[a](/x/)\n")

    def test_mailto_and_tel(self):
        self.assertMarkdown(
            "<p><a href='mailto:a@b.c'>m</a> <a href='tel:+44'>t</a></p>",
            "[m](mailto:a@b.c) [t](tel:+44)\n",
        )

    def test_unsafe_schemes_unwrapped(self):
        self.assertMarkdown(
            "<p><a href='javascript:alert(1)'>js</a> "
            "<a href='JaVa\tscript:alert(1)'>js2</a> "
            "<a href='data:text/html,x'>data</a></p>",
            "js js2 data\n",
        )

    def test_missing_or_empty_href_unwrapped(self):
        self.assertMarkdown("<p><a>none</a> <a href=''>empty</a></p>", "none empty\n")

    def test_empty_link_text_dropped(self):
        self.assertMarkdown("<p><a href='/x'></a>after</p>", "after\n")

    def test_destination_escaped(self):
        self.assertMarkdown(
            "<p><a href='https://x.com/a_(b) c'>p</a></p>",
            "[p](https://x.com/a_\\(b\\)%20c)\n",
        )

    def test_link_text_escaped(self):
        self.assertMarkdown(
            "<p><a href='/x'>[b] *s*</a></p>",
            "[\\[b\\] \\*s\\*](https://example.com/x)\n",
        )

    def test_styled_link_text(self):
        self.assertMarkdown(
            "<p><a href='/x'><strong>bold</strong></a></p>",
            "[**bold**](https://example.com/x)\n",
        )

    def test_link_wrapping_blocks_applied_to_each_block(self):
        # The "card" pattern
        self.assertMarkdown(
            "<a href='/c'><div><h3>Title</h3><p>Text</p></div></a>",
            "### [Title](https://example.com/c)\n\n[Text](https://example.com/c)\n",
        )

    def test_heading_permalinks_removed(self):
        self.assertMarkdown(
            "<h2>Title<a class='headerlink' href='#title'>¶</a></h2>"
            "<h3><a href='#sub'>#</a> Sub</h3><p><a href='#title'>Back to title</a></p>",
            "## Title\n\n### Sub\n\n[Back to title](https://example.com/blog/#title)\n",
        )

    def test_script_inside_link_removed(self):
        self.assertMarkdown(
            "<a href='/x'>t<script>bad()</script></a>", "[t](https://example.com/x)\n"
        )

    def test_link_wrapping_code_block(self):
        self.assertMarkdown("<a href='/x'><pre>code</pre></a>", "```\ncode\n```\n")


class TestLists(HTMLToMarkdownTestCase):
    def test_unordered(self):
        self.assertMarkdown("<ul><li>a</li><li>b</li></ul>", "- a\n- b\n")

    def test_ordered(self):
        self.assertMarkdown("<ol><li>a</li><li>b</li></ol>", "1. a\n2. b\n")

    def test_nested(self):
        self.assertMarkdown(
            "<ul><li>1<ul><li>2<ul><li>3<ul><li>4</li></ul></li></ul></li></ul></li></ul>",
            "- 1\n  - 2\n    - 3\n      - 4\n",
        )

    def test_mixed_nesting(self):
        self.assertMarkdown(
            "<ul><li>a<ol><li>x</li><li>y</li></ol></li><li>b</li></ul>",
            "- a\n  1. x\n  2. y\n- b\n",
        )

    def test_inline_content(self):
        self.assertMarkdown(
            "<ul><li><strong>b</strong> <a href='/x'>l</a></li></ul>",
            "- **b** [l](/x)\n",
        )

    def test_paragraphs_in_item(self):
        self.assertMarkdown(
            "<ul><li><p>p1</p><p>p2</p></li><li><p>single</p></li></ul>",
            "- p1\\\np2\n- single\n",
        )

    def test_heading_in_item(self):
        self.assertMarkdown("<ul><li><h3>H</h3>text</li></ul>", "- H\\\ntext\n")

    def test_link_wrapping_heading_in_item(self):
        self.assertMarkdown(
            "<ul><li><a href='/x'><h3>T</h3></a></li></ul>", "- [T](/x)\n"
        )

    def test_image_in_item(self):
        self.assertMarkdown(
            "<ul><li>Text <img src='/a.png' alt='A'></li></ul>",
            "- Text ![A](/a.png)\n",
        )

    def test_card_markup_in_item(self):
        self.assertMarkdown(
            "<ul><li><div><img src='/a.png' alt=''></div>"
            "<div><a href='/x'>Title</a><p>Author</p></div></li></ul>",
            "- ![](/a.png)\\\n[Title](/x)\\\nAuthor\n",
        )

    def test_table_in_item_flattened(self):
        self.assertMarkdown(
            "<ul><li><table><tr><td>a</td><td>b</td></tr><tr><td>c</td><td>d</td></tr>"
            "</table></li></ul>",
            "- a · b<br>c · d\n",
        )

    def test_nested_ordered_list(self):
        self.assertMarkdown(
            "<ol><li>one</li><li>two<ol><li>sub</li></ol></li><li>three</li></ol>",
            "1. one\n2. two\n   1. sub\n3. three\n",
        )

    def test_table_after_text_in_item(self):
        self.assertMarkdown(
            "<ul><li>Text:<table><tr><td>x</td><td>y</td></tr></table></li></ul>",
            "- Text:\\\nx · y\n",
        )

    def test_card_link_with_table_in_item(self):
        # bakerydemo's listing cards
        self.assertMarkdown(
            "<ul><li><a href='/b/'><div><h2>Bolani</h2><table>"
            "<tr><th>Origin</th><td>Afghanistan</td></tr></table></div></a></li></ul>",
            "- [Bolani](/b/)\\\n[Origin · Afghanistan](/b/)\n",
        )

    def test_adjacent_lists_of_different_types(self):
        self.assertMarkdown("<ul><li>a</li></ul><ol><li>b</li></ol>", "- a\n\n1. b\n")

    def test_orphan_list_item(self):
        self.assertMarkdown("<li>orphan</li>", "- orphan\n")

    def test_empty_lists_and_items_dropped(self):
        self.assertMarkdown("<ul></ul><ul><li></li><li> </li></ul><p>x</p>", "x\n")

    def test_hr_in_item(self):
        self.assertMarkdown("<ul><li>a<hr>b</li></ul>", "- a\\\nb\n")

    def test_list_inside_paragraph(self):
        self.assertMarkdown(
            "<p>before<ul><li>item</li></ul>after</p>", "before\n\n- item\n\nafter\n"
        )


class TestBlockquotes(HTMLToMarkdownTestCase):
    def test_paragraphs_form_one_quote(self):
        self.assertMarkdown(
            "<blockquote><p>one</p><p>two</p></blockquote><p>x</p>"
            "<blockquote>three</blockquote>",
            "> one\n>\n> two\n\nx\n\n> three\n",
        )

    def test_line_break(self):
        self.assertMarkdown("<blockquote>a<br>b</blockquote>", "> a\\\nb\n")

    def test_simple(self):
        self.assertMarkdown("<blockquote>Quote</blockquote>", "> Quote\n")

    def test_paragraph(self):
        self.assertMarkdown("<blockquote><p>Quote</p></blockquote>", "> Quote\n")

    def test_inline_content(self):
        self.assertMarkdown(
            "<blockquote><p><em>i</em> <a href='/x'>l</a></p></blockquote>",
            "> *i* [l](/x)\n",
        )

    def test_heading_in_quote(self):
        self.assertMarkdown("<blockquote><h2>H</h2></blockquote>", "> H\n")

    def test_attribution(self):
        self.assertMarkdown(
            "<blockquote><p>Q</p><footer>— <cite>Author</cite></footer></blockquote>",
            "> Q\n>\n> — *Author*\n",
        )

    def test_code_block_in_quote(self):
        self.assertMarkdown(
            "<blockquote><pre>code\n\n  more  </pre></blockquote><p>after</p>",
            "> ```\n> code\n> \n>   more  \n> ```\n\nafter\n",
        )

    def test_table_in_quote(self):
        self.assertMarkdown(
            "<blockquote><p>q</p><table><tr><th>h</th></tr><tr><td>a</td></tr>"
            "</table></blockquote>",
            "> q\n>\n> | h |\n> | --- |\n> | a |\n",
        )


class TestPreformatted(HTMLToMarkdownTestCase):
    def test_language_from_class(self):
        self.assertMarkdown(
            "<pre><code class='language-python'>x</code></pre>"
            "<pre class='lang-css'>a {}</pre>",
            "```python\nx\n```\n\n```css\na {}\n```\n",
        )

    def test_in_table_cell(self):
        self.assertMarkdown(
            "<table><tr><td><pre>a\nb</pre></td></tr></table>", "| `a b` |\n| --- |\n"
        )

    def test_trailing_whitespace_preserved(self):
        self.assertMarkdown(
            "<pre>a   \nb\xa0</pre><p>x&nbsp;</p>", "```\na   \nb\xa0\n```\n\nx\n"
        )

    def test_whitespace_preserved(self):
        self.assertMarkdown(
            "<pre>  indented\n\ttab\n\nblank above</pre>",
            "```\n  indented\n\ttab\n\nblank above\n```\n",
        )

    def test_leading_newline_ignored(self):
        self.assertMarkdown("<pre>\nfirst</pre>", "```\nfirst\n```\n")

    def test_not_escaped(self):
        self.assertMarkdown(
            "<pre>*a* &lt;div&gt; &amp;&amp; # h</pre>",
            "```\n*a* <div> && # h\n```\n",
        )

    def test_fence_longer_than_content_backticks(self):
        self.assertMarkdown(
            "<pre>```\ninner\n```</pre>", "````\n```\ninner\n```\n````\n"
        )

    def test_syntax_highlighting_markup_stripped(self):
        self.assertMarkdown(
            "<div class='highlight'><pre><code class='language-js'>"
            "<span class='k'>const</span> a = <span>1</span>;</code></pre></div>",
            "```js\nconst a = 1;\n```\n",
        )

    def test_in_list_item(self):
        self.assertMarkdown(
            "<ul><li>Run:<pre>npm test</pre></li></ul>", "- Run:\\\n`npm test`\n"
        )


class TestImages(HTMLToMarkdownTestCase):
    base_url = "https://example.com/blog/"

    def test_block_image(self):
        self.assertMarkdown(
            "<img src='https://cdn.example.com/a.jpg' alt='A'>",
            "![A](https://cdn.example.com/a.jpg)\n",
        )

    def test_relative_src_made_absolute(self):
        self.assertMarkdown(
            "<p><img src='/a.jpg' alt='A'></p>", "![A](https://example.com/a.jpg)\n"
        )

    def test_missing_alt(self):
        self.assertMarkdown("<img src='/a.jpg'>", "![](https://example.com/a.jpg)\n")

    def test_alt_escaped(self):
        self.assertMarkdown(
            "<img src='/a.jpg' alt='a [b] *c*'>",
            "![a \\[b\\] \\*c\\*](https://example.com/a.jpg)\n",
        )

    def test_inline_image(self):
        self.assertMarkdown(
            "<p>before <img src='/a.jpg' alt='A'> after</p>",
            "before ![A](https://example.com/a.jpg) after\n",
        )

    def test_lazy_loaded_and_srcset(self):
        self.assertMarkdown(
            "<img data-src='/lazy.jpg' alt='L'><img srcset='/s.jpg 1x, /l.jpg 2x' alt='S'>",
            "![L](https://example.com/lazy.jpg)\n\n![S](https://example.com/s.jpg)\n",
        )

    def test_picture(self):
        self.assertMarkdown(
            "<picture><source srcset='/a.webp'><img src='/a.jpg' alt='P'></picture>",
            "![P](https://example.com/a.jpg)\n",
        )

    def test_figure_with_caption(self):
        self.assertMarkdown(
            "<figure><img src='/a.jpg' alt='A'><figcaption>Cap <em>e</em></figcaption></figure>",
            "![A](https://example.com/a.jpg)\n\nCap *e*\n",
        )

    def test_unsafe_or_data_src_dropped(self):
        self.assertMarkdown(
            "<img src='javascript:alert(1)' alt='x'>"
            "<img src='data:image/png;base64,AAAA' alt='y'><img alt='z'><p>ok</p>",
            "ok\n",
        )

    def test_linked_image(self):
        self.assertMarkdown(
            "<a href='/x'><img src='/a.jpg' alt='A'></a>",
            "[![A](https://example.com/a.jpg)](https://example.com/x)\n",
        )

    def test_linked_image_with_text_keeps_text(self):
        self.assertMarkdown(
            "<a href='/x'><img src='/a.jpg' alt='A'> Text</a>",
            "[Text](https://example.com/x)\n",
        )

    def test_image_with_unsafe_link(self):
        self.assertMarkdown(
            "<a href='javascript:x'><img src='/a.jpg' alt='A'></a>",
            "![A](https://example.com/a.jpg)\n",
        )


class TestMedia(HTMLToMarkdownTestCase):
    def test_iframe(self):
        self.assertMarkdown(
            "<iframe src='https://www.youtube.com/embed/x' title='Video'></iframe>",
            "[Video](https://www.youtube.com/embed/x)\n",
        )

    def test_video_and_audio(self):
        self.assertMarkdown(
            "<video src='/v.mp4' title='Vid'></video>"
            "<video><source src='/v2.mp4'></video><audio src='/a.mp3'></audio>",
            "[Vid](/v.mp4)\n\n[/v2.mp4](/v2.mp4)\n\n[/a.mp3](/a.mp3)\n",
        )

    def test_without_source_dropped(self):
        self.assertMarkdown("<iframe></iframe><video></video><p>x</p>", "x\n")

    def test_object_and_embed_dropped(self):
        self.assertMarkdown(
            "<object data='/x'></object><embed src='/y'><p>x</p>", "x\n"
        )


class TestHorizontalRules(HTMLToMarkdownTestCase):
    def test_hr(self):
        self.assertMarkdown("<p>a</p><hr><p>b</p>", "a\n\n---\n\nb\n")


class TestTables(HTMLToMarkdownTestCase):
    def test_basic(self):
        self.assertMarkdown(
            "<table><tr><th>H1</th><th>H2</th></tr><tr><td>a</td><td>b</td></tr></table>",
            "| H1 | H2 |\n| --- | --- |\n| a | b |\n",
        )

    def test_sections(self):
        self.assertMarkdown(
            "<table><thead><tr><th>H</th></tr></thead><tbody><tr><td>b</td></tr></tbody>"
            "<tfoot><tr><td>f</td></tr></tfoot></table>",
            "| H |\n| --- |\n| b |\n| f |\n",
        )

    def test_first_row_used_as_header(self):
        self.assertMarkdown(
            "<table><tr><td>a</td><td>b</td></tr><tr><td>c</td><td>d</td></tr></table>",
            "| a | b |\n| --- | --- |\n| c | d |\n",
        )

    def test_colspan_padded(self):
        self.assertMarkdown(
            "<table><tr><th colspan='2'>Wide</th></tr><tr><td>a</td><td>b</td></tr></table>",
            "| Wide | |\n| --- | --- |\n| a | b |\n",
        )

    def test_colspan_capped(self):
        markdown = html_to_markdown(
            "<table><tr><td colspan='1000000'>x</td></tr></table>"
        )
        self.assertEqual(markdown.split("\n")[0].count("|"), 1001)

    def test_line_break_in_cell(self):
        self.assertMarkdown(
            "<table><tr><td>a<br>b</td><td>c\\<br>d</td></tr></table>",
            "| a<br>b | c\\\\<br>d |\n| --- | --- |\n",
        )

    def test_ragged_rows_padded(self):
        self.assertMarkdown(
            "<table><tr><td>a</td></tr><tr><td>b</td><td>c</td></tr></table>",
            "| a | |\n| --- | --- |\n| b | c |\n",
        )

    def test_rich_cells(self):
        self.assertMarkdown(
            "<table><tr><th>K</th></tr><tr><td><p>p1</p><p>p2</p>"
            "<a href='/x'>l</a> <img src='/i.png' alt='i'> <code>a|b</code></td></tr></table>",
            "| K |\n| --- |\n| p1<br>p2<br>[l](/x) ![i](/i.png) `a\\|b` |\n",
        )

    def test_pipe_escaped(self):
        self.assertMarkdown(
            "<table><tr><td>a|b</td></tr></table>", "| a\\|b |\n| --- |\n"
        )

    def test_no_line_start_escapes_in_cells(self):
        self.assertMarkdown(
            "<table><tr><td>350.0</td><td># tag</td><td>- x</td><td>1) a</td>"
            "<td>&gt; q</td><td>a|b</td></tr></table>",
            "| 350.0 | # tag | - x | 1) a | > q | a\\|b |\n"
            "| --- | --- | --- | --- | --- | --- |\n",
        )

    def test_caption(self):
        self.assertMarkdown(
            "<table><caption>Cap</caption><tr><td>a</td></tr></table>",
            "**Cap**\n\n| a |\n| --- |\n",
        )

    def test_nested_table_flattened(self):
        self.assertMarkdown(
            "<table><tr><th>Outer</th></tr><tr><td><table><tr><td>a</td><td>b</td></tr>"
            "<tr><td>c</td><td>d</td></tr></table></td></tr></table>",
            "| Outer |\n| --- |\n| a · b<br>c · d |\n",
        )

    def test_empty(self):
        self.assertMarkdown("<table></table><p>x</p>", "x\n")

    def test_inside_container(self):
        self.assertMarkdown(
            "<p>Before</p><div><table><tr><td>x</td></tr></table></div><p>After</p>",
            "Before\n\n| x |\n| --- |\n\nAfter\n",
        )


class TestOtherBlocks(HTMLToMarkdownTestCase):
    def test_definition_list(self):
        self.assertMarkdown(
            "<dl><dt>T1</dt><dd>D1</dd><dd>D1b</dd><dt>T2</dt><dd><p>P</p></dd></dl>",
            "**T1**\n\nD1\n\nD1b\n\n**T2**\n\nP\n",
        )

    def test_details(self):
        self.assertMarkdown(
            "<details><summary>More</summary><p>Content</p></details>",
            "**More**\n\nContent\n",
        )

    def test_address(self):
        self.assertMarkdown("<address>1 Road<br>Town</address>", "1 Road\\\nTown\n")


class TestContainers(HTMLToMarkdownTestCase):
    def test_nested_divs(self):
        self.assertMarkdown(
            "<div><div><div>Deep</div></div></div><div>Sibling <span>s</span></div>",
            "Deep\n\nSibling s\n",
        )

    def test_loose_text_around_blocks(self):
        self.assertMarkdown(
            "<div>loose<p>para</p>more</div>", "loose\n\npara\n\nmore\n"
        )

    def test_sectioning_elements(self):
        self.assertMarkdown(
            "<article><section><header><h2>H</h2></header><p>x</p>"
            "<aside><p>Callout</p></aside><footer>by me</footer></section></article>",
            "## H\n\nx\n\nCallout\n\nby me\n",
        )

    def test_inline_element_wrapping_blocks(self):
        self.assertMarkdown("<strong><p>a</p><p>b</p></strong>", "**a**\n\n**b**\n")

    def test_paragraph_inside_paragraph(self):
        self.assertMarkdown(
            "<p>outer <p>inner</p> tail</p>", "outer\n\ninner\n\ntail\n"
        )

    def test_custom_elements_unwrapped(self):
        self.assertMarkdown(
            "<my-widget>Custom <b>el</b></my-widget><p>x</p>", "Custom **el**\n\nx\n"
        )

    def test_attributes_ignored(self):
        self.assertMarkdown(
            "<p style='color:red' class='lead' id='i' data-block-key='k'>p</p>", "p\n"
        )


class TestNonContent(HTMLToMarkdownTestCase):
    def test_scripts_and_styles_removed_with_content(self):
        self.assertMarkdown(
            "<script>alert(1)</script><style>p{}</style><noscript>JS</noscript>"
            "<template><p>T</p></template><p>ok</p>",
            "ok\n",
        )

    def test_comments_removed(self):
        self.assertMarkdown("<p>a<!-- c -->b</p><!-- top -->", "ab\n")

    def test_hidden_elements_removed(self):
        self.assertMarkdown(
            "<p hidden>h1</p><p aria-hidden='true'>h2</p><p style='display: none'>h3</p>"
            "<p>visible <span aria-hidden='true'>★</span></p>",
            "visible\n",
        )

    def test_form_controls_removed(self):
        self.assertMarkdown(
            "<form><label>Name <input name='n'></label><select><option>o</option>"
            "</select><textarea>t</textarea><button>Go</button><p>Help</p></form>",
            "Name\n\nHelp\n",
        )

    def test_svg_and_math_removed(self):
        self.assertMarkdown(
            "<p><svg><title>icon</title></svg> Label <math><mi>x</mi></math></p>",
            "Label\n",
        )

    def test_data_markdown_ignore(self):
        self.assertMarkdown(
            "<div data-markdown-ignore><p>Breadcrumbs</p></div>"
            "<p>Body <span data-markdown-ignore>(share)</span></p>",
            "Body\n",
        )

    def test_navigation_removed(self):
        self.assertMarkdown("<nav><a href='/'>Home</a></nav><p>x</p>", "x\n")


class TestContentSelection(HTMLToMarkdownTestCase):
    def test_full_document_uses_body(self):
        self.assertMarkdown(
            "<!DOCTYPE html><html><head><title>T</title><style>x</style></head>"
            "<body><p>Body</p></body></html>",
            "Body\n",
        )

    def test_main_preferred(self):
        self.assertMarkdown(
            "<body><header>Site</header><main><p>Main</p></main><footer>F</footer></body>",
            "Main\n",
        )

    def test_content_selector(self):
        self.assertEqual(
            html_to_markdown(
                "<main><div class='ad'>Ad</div><div id='content'><p>C</p></div></main>",
                content_selector="#content",
            ),
            "C\n",
        )

    def test_content_selector_not_found_falls_back(self):
        self.assertEqual(
            html_to_markdown("<main><p>M</p></main>", content_selector="#nope"), "M\n"
        )


class TestMalformedHTML(HTMLToMarkdownTestCase):
    def test_unclosed_tags(self):
        self.assertMarkdown(
            "<p>unclosed <strong>bold<p>next", "unclosed\n\n**bold**\n\n**next**\n"
        )

    def test_misnested_tags(self):
        self.assertMarkdown("<p><strong><em>x</strong></em></p>", "***x***\n")

    def test_stray_end_tags(self):
        self.assertMarkdown("</div></p>text</span>", "text\n")

    def test_nested_duplicate_inline_elements(self):
        self.assertMarkdown(
            "<p><b>a <b>b</b></b> <a href='https://x.com'>c "
            "<a href='https://y.com'>d</a></a></p>",
            "**a b** [c d](https://x.com)\n",
        )

    def test_blocks_nested_in_blocks(self):
        self.assertMarkdown("<h3>a<em><h1>t</h1></em></h3>", "### a\n\n# *t*\n")
        self.assertMarkdown("<p><b><p>x</p></b></p>", "**x**\n")

    def test_table_cells_outside_table(self):
        self.assertMarkdown("<em><td>a</td><th>b</th></em>", "*ab*\n")

    def test_list_item_inside_inline_element(self):
        self.assertMarkdown("<a href='https://x.com'><s><li>y</li></s></a>", "- y\n")

    def test_deep_nesting(self):
        self.assertMarkdown("<b><i>" * 400 + "x", "***x***\n")
        markdown = html_to_markdown("<ul><li>" * 200 + "x")
        self.assertTrue(markdown.endswith("\n" + " " * 18 + "- x\n"))


class TestKnownLimitations(HTMLToMarkdownTestCase):
    """Current behaviour for constructs the pipeline cannot represent. These
    pin down the MVP's limitations rather than desired output."""

    def test_ordered_list_start_lost(self):
        # Contentstate list items carry no start number.
        self.assertMarkdown("<ol start='5'><li>five</li></ol>", "1. five\n")

    def test_list_inside_quote_loses_quote(self):
        self.assertMarkdown("<blockquote><ul><li>a</li></ul></blockquote>", "- a\n")

    def test_adjacent_emphasis_runs(self):
        # Styles are rendered per text segment: an italic run split by a bold
        # segment produces adjacent delimiters, which CommonMark misreads.
        self.assertMarkdown(
            "<p><em>it <strong>b</strong>.</em></p>", "*it* ***b****.*\n"
        )

    def test_rowspan_not_represented(self):
        self.assertMarkdown(
            "<table><tr><th>A</th><th>B</th></tr><tr><td rowspan='2'>r</td><td>1</td></tr>"
            "<tr><td>2</td></tr></table>",
            "| A | B |\n| --- | --- |\n| r | 1 |\n| 2 | |\n",
        )

    def test_text_after_nested_list_becomes_nested_item(self):
        self.assertMarkdown(
            "<ul><li>before<ul><li>nested</li></ul>after</li></ul>",
            "- before\n  - nested\n  - after\n",
        )

    def test_page_chrome_without_main_included(self):
        self.assertMarkdown(
            "<body><header>Site</header><p>Body</p><footer>Footer</footer></body>",
            "Site\n\nBody\n\nFooter\n",
        )

    def test_db_html_references_not_resolved(self):
        # Rendered HTML is the input; DB HTML goes through MarkdownConverter.
        self.assertMarkdown(
            "<p><a linktype='page' id='2'>page</a></p>"
            "<embed embedtype='image' id='1' format='left'/>",
            "page\n",
        )


class TestWagtailRenderedHTML(PageFixturesMixin, TestCase):
    """HTML as Wagtail renders it: rich text with expanded references, and
    the default rendering of StreamField blocks."""

    fixtures = ["test.json"]

    def test_rich_text_references(self):
        page = Page.objects.get(url_path="/home/events/")
        image = get_image_model().objects.create(
            title="Test image", file=get_test_image_file()
        )
        document = Document.objects.create(
            title="Test doc", file=ContentFile(b"doc", name="doc.txt")
        )
        embed = Embed(
            url="https://www.youtube.com/watch?v=x",
            html='<iframe src="https://www.youtube.com/embed/x" title="A video"></iframe>',
            type="video",
            width=480,
            height=270,
        )
        db_html = (
            f'<p><a linktype="page" id="{page.id}">Events</a>, '
            f'<a linktype="document" id="{document.id}">a document</a> and '
            '<a linktype="page" id="999999">a broken link</a>.</p>'
            f'<embed embedtype="image" id="{image.id}" format="left" alt="Alt text"/>'
            '<embed embedtype="media" url="https://www.youtube.com/watch?v=x"/>'
        )
        with patch("wagtail.embeds.embeds.get_embed", return_value=embed):
            html = expand_db_html(db_html)

        markdown = html_to_markdown(html, base_url="http://localhost/")

        self.assertEqual(
            markdown.split("\n\n")[0],
            f"[Events](http://localhost/events/), "
            f"[a document](http://localhost{document.url}) and a broken link.",
        )
        self.assertRegex(
            markdown,
            r"\n\n!\[Alt text\]\(http://localhost/media/images/test[^)]*\.png\)\n\n",
        )
        self.assertTrue(
            markdown.endswith("[A video](https://www.youtube.com/embed/x)\n")
        )

    def test_streamfield_default_rendering(self):
        class PersonBlock(blocks.StructBlock):
            name = blocks.CharBlock()
            bio = blocks.RichTextBlock()

        stream_block = blocks.StreamBlock(
            [
                ("heading", blocks.CharBlock()),
                ("paragraph", blocks.RichTextBlock()),
                ("person", PersonBlock()),
                ("links", blocks.ListBlock(blocks.URLBlock())),
                ("quote", blocks.BlockQuoteBlock()),
                ("table", TableBlock()),
                (
                    "typed_table",
                    TypedTableBlock(
                        [
                            ("text", blocks.CharBlock()),
                            ("number", blocks.IntegerBlock()),
                        ]
                    ),
                ),
            ]
        )
        value = stream_block.to_python(
            [
                {"type": "heading", "value": "A heading"},
                {
                    "type": "paragraph",
                    "value": "<h2>Rich text</h2><p>Some <b>bold</b> text.</p>"
                    "<ol><li>one</li><li>two</li></ol>",
                },
                {
                    "type": "person",
                    "value": {"name": "Ada", "bio": "<p>Wrote notes.</p>"},
                },
                {"type": "links", "value": ["https://a.example", "https://b.example"]},
                {"type": "quote", "value": "To be or not to be"},
                {
                    "type": "table",
                    "value": {
                        "data": [["H1", "H2"], ["a", "b"]],
                        "first_row_is_table_header": True,
                    },
                },
                {
                    "type": "typed_table",
                    "value": {
                        "columns": [
                            {"type": "text", "heading": "Name"},
                            {"type": "number", "heading": "Qty"},
                        ],
                        "rows": [{"values": ["Rye", 3]}],
                    },
                },
            ]
        )

        self.assertEqual(
            html_to_markdown(value.render_as_block()),
            "A heading\n\n"
            "## Rich text\n\nSome **bold** text.\n\n1. one\n2. two\n\n"
            "**name**\n\nAda\n\n**bio**\n\nWrote notes.\n\n"
            "- https://a.example\n- https://b.example\n\n"
            "> To be or not to be\n\n"
            "| H1 | H2 |\n| --- | --- |\n| a | b |\n\n"
            "| Name | Qty |\n| --- | --- |\n| Rye | 3 |\n",
        )
