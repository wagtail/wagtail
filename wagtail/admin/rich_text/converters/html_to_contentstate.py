import re
from html.parser import HTMLParser

from wagtail.admin.rich_text.converters.contentstate_models import (
    Block,
    ContentState,
    Entity,
    EntityRange,
    InlineStyleRange,
)
from wagtail.admin.rich_text.converters.html_ruleset import HTMLRuleset
from wagtail.models import Page
from wagtail.rich_text import features as feature_registry

# constants to keep track of what to do with leading whitespace on the next text node we encounter
STRIP_WHITESPACE = 0
KEEP_WHITESPACE = 1
FORCE_WHITESPACE = 2

# match one or more consecutive normal spaces, new-lines, tabs and form-feeds
WHITESPACE_RE = re.compile(r"[ \t\n\f\r]+")

# the attribute name to persist the Draftail block key between FE and db
BLOCK_KEY_NAME = "data-block-key"


class HandlerState:
    def __init__(self):
        self.current_block = None
        self.current_inline_styles = []
        self.current_entity_ranges = []

        # what to do with leading whitespace on the next text node we encounter: strip, keep or force
        self.leading_whitespace = STRIP_WHITESPACE
        self.list_depth = 0
        self.list_item_type = None

        # an atomic block which is NOT preceded by a non-atomic block must have a spacer
        # paragraph inserted before it
        # NB This is not included in pushed/popped state, because after a pop() this
        # should still indicate the status of the most recent block, not the one preceding
        # the corresponding push()
        self.has_preceding_nonatomic_block = False

        self.pushed_states = []

    def push(self):
        self.pushed_states.append(
            {
                "current_block": self.current_block,
                "current_inline_styles": self.current_inline_styles,
                "current_entity_ranges": self.current_entity_ranges,
                "leading_whitespace": self.leading_whitespace,
                "list_depth": self.list_depth,
                "list_item_type": self.list_item_type,
            }
        )

    def pop(self):
        last_state = self.pushed_states.pop()
        self.current_block = last_state["current_block"]
        self.current_inline_styles = last_state["current_inline_styles"]
        self.current_entity_ranges = last_state["current_entity_ranges"]
        self.leading_whitespace = last_state["leading_whitespace"]
        self.list_depth = last_state["list_depth"]
        self.list_item_type = last_state["list_item_type"]


def add_paragraph_block(state, contentstate):
    """
    Utility function for adding an unstyled (paragraph) block to contentstate;
    useful for element handlers that aren't paragraph elements themselves, but need
    to insert paragraphs to ensure correctness
    """
    block = Block("unstyled", depth=state.list_depth)
    contentstate.blocks.append(block)
    state.current_block = block
    state.leading_whitespace = STRIP_WHITESPACE
    state.has_preceding_nonatomic_block = True


class ListElementHandler:
    """Handler for <ul> / <ol> tags"""

    def __init__(self, list_item_type):
        self.list_item_type = list_item_type

    def handle_starttag(self, name, attrs, state, contentstate):
        state.push()

        if state.list_item_type is None:
            # this is not nested in another list => depth remains unchanged
            pass
        else:
            # start the next nesting level
            state.list_depth += 1

        state.list_item_type = self.list_item_type

    def handle_endtag(self, name, state, contentstate):
        state.pop()


class BlockElementHandler:
    def __init__(self, block_type):
        self.block_type = block_type

    def create_block(self, name, attrs, state, contentstate):
        return Block(
            self.block_type, depth=state.list_depth, key=attrs.get(BLOCK_KEY_NAME)
        )

    def handle_starttag(self, name, attrs, state, contentstate):
        attr_dict = dict(
            attrs
        )  # convert attrs from list of (name, value) tuples to a dict
        block = self.create_block(name, attr_dict, state, contentstate)
        contentstate.blocks.append(block)
        state.current_block = block
        state.leading_whitespace = STRIP_WHITESPACE
        state.has_preceding_nonatomic_block = True

    def handle_endtag(self, name, state, contentState):
        assert not state.current_inline_styles, (
            "End of block reached without closing inline style elements"
        )
        assert not state.current_entity_ranges, (
            "End of block reached without closing entity elements"
        )
        state.current_block = None


class ListItemElementHandler(BlockElementHandler):
    """Handler for <li> tag"""

    def __init__(self):
        pass  # skip setting self.block_type

    def create_block(self, name, attrs, state, contentstate):
        assert state.list_item_type is not None, (
            "%s element found outside of an enclosing list element" % name
        )
        return Block(
            state.list_item_type, depth=state.list_depth, key=attrs.get(BLOCK_KEY_NAME)
        )


class InlineStyleElementHandler:
    def __init__(self, style):
        self.style = style

    def handle_starttag(self, name, attrs, state, contentstate):
        if state.current_block is None:
            # Inline style element encountered at the top level -
            # start a new paragraph block to contain it
            add_paragraph_block(state, contentstate)

        if state.leading_whitespace == FORCE_WHITESPACE:
            # any pending whitespace should be output before handling this tag,
            # and subsequent whitespace should be collapsed into it (= stripped)
            state.current_block.text += " "
            state.leading_whitespace = STRIP_WHITESPACE

        inline_style_range = InlineStyleRange(self.style)
        inline_style_range.offset = len(state.current_block.text)
        state.current_block.inline_style_ranges.append(inline_style_range)
        state.current_inline_styles.append(inline_style_range)

    def handle_endtag(self, name, state, contentstate):
        inline_style_range = state.current_inline_styles.pop()
        assert inline_style_range.style == self.style
        inline_style_range.length = (
            len(state.current_block.text) - inline_style_range.offset
        )


class InlineEntityElementHandler:
    """
    Abstract superclass for elements that will be represented as inline entities.
    Subclasses should define a `mutability` property
    """

    def __init__(self, entity_type):
        self.entity_type = entity_type

    def handle_starttag(self, name, attrs, state, contentstate):
        if state.current_block is None:
            # Inline entity element encountered at the top level -
            # start a new paragraph block to contain it
            add_paragraph_block(state, contentstate)

        if state.leading_whitespace == FORCE_WHITESPACE:
            # any pending whitespace should be output before handling this tag,
            # and subsequent whitespace should be collapsed into it (= stripped)
            state.current_block.text += " "
            state.leading_whitespace = STRIP_WHITESPACE

        # convert attrs from a list of (name, value) tuples to a dict
        # for get_attribute_data to work with
        attrs = dict(attrs)

        entity = Entity(
            self.entity_type, self.mutability, self.get_attribute_data(attrs)
        )
        key = contentstate.add_entity(entity)

        entity_range = EntityRange(key)
        entity_range.offset = len(state.current_block.text)
        state.current_block.entity_ranges.append(entity_range)
        state.current_entity_ranges.append(entity_range)

    def get_attribute_data(self, attrs):
        """
        Given a dict of attributes found on the source element, return the data dict
        to be associated with the resulting entity
        """
        return {}

    def handle_endtag(self, name, state, contentstate):
        entity_range = state.current_entity_ranges.pop()
        entity_range.length = len(state.current_block.text) - entity_range.offset


class LinkElementHandler(InlineEntityElementHandler):
    mutability = "MUTABLE"


class ExternalLinkElementHandler(LinkElementHandler):
    def get_attribute_data(self, attrs):
        return {"url": attrs["href"]}


class PageLinkElementHandler(LinkElementHandler):
    def get_attribute_data(self, attrs):
        try:
            page = Page.objects.get(id=attrs["id"]).specific
        except Page.DoesNotExist:
            # retain ID so that it's still identified as a page link (albeit a broken one)
            return {"id": int(attrs["id"]), "url": None, "parentId": None}

        parent_page = page.get_parent()

        return {
            "id": page.id,
            "url": page.url,
            "parentId": parent_page.id if parent_page else None,
        }


class AtomicBlockEntityElementHandler:
    """
    Handler for elements like <img> that exist as a single immutable item at the block level
    """

    def handle_starttag(self, name, attrs, state, contentstate):
        if state.current_block:
            # Placing an atomic block inside another block (e.g. a paragraph) is invalid in
            # contentstate; we will recover from this by forcibly closing the block along with all
            # of its inline styles / entities, and opening a new identical one afterwards.

            # Construct a new block of the same type and depth as the currently open one; this will
            # become the new 'current block' after we've added the atomic block.
            next_block = Block(
                state.current_block.type, depth=state.current_block.depth
            )

            for inline_style_range in state.current_inline_styles:
                # set this inline style to end at the current text position
                inline_style_range.length = (
                    len(state.current_block.text) - inline_style_range.offset
                )
                # start a new one of the same type, which will begin at the next block
                new_inline_style = InlineStyleRange(inline_style_range.style)
                new_inline_style.offset = 0
                next_block.inline_style_ranges.append(new_inline_style)

            for entity_range in state.current_entity_ranges:
                # set this inline entity to end at the current text position
                entity_range.length = (
                    len(state.current_block.text) - entity_range.offset
                )
                # start a new entity range, pointing to the same entity, to begin at the next block
                new_entity_range = EntityRange(entity_range.key)
                new_entity_range.offset = 0
                next_block.entity_ranges.append(new_entity_range)

            state.current_block = None
        else:
            next_block = None

        if not state.has_preceding_nonatomic_block:
            # if this block is NOT preceded by a non-atomic block,
            # need to insert a spacer paragraph
            add_paragraph_block(state, contentstate)
            # immediately set this as not the current block, so that any subsequent invocations
            # of this handler don't think we're inside it
            state.current_block = None

        attr_dict = dict(
            attrs
        )  # convert attrs from list of (name, value) tuples to a dict
        entity = self.create_entity(name, attr_dict, state, contentstate)
        key = contentstate.add_entity(entity)

        block = Block("atomic", depth=state.list_depth)
        contentstate.blocks.append(block)
        block.text = " "
        entity_range = EntityRange(key)
        entity_range.offset = 0
        entity_range.length = 1
        block.entity_ranges.append(entity_range)
        state.has_preceding_nonatomic_block = False

        if next_block:
            # take the replica that we made of the previous block and its inline styles / entities,
            # and make that the new current block. Now, when we encounter the closing tags for
            # those styles/entities further on in the document, they will close the range that
            # began here.
            contentstate.blocks.append(next_block)
            state.current_block = next_block
            state.current_inline_styles = next_block.inline_style_ranges.copy()
            state.current_entity_ranges = next_block.entity_ranges.copy()
            state.has_preceding_nonatomic_block = True
            state.leading_whitespace = STRIP_WHITESPACE

    def handle_endtag(self, name, state, contentstate):
        pass


class HorizontalRuleHandler(AtomicBlockEntityElementHandler):
    def create_entity(self, name, attrs, state, contentstate):
        return Entity("HORIZONTAL_RULE", "IMMUTABLE", {})


class LineBreakHandler:
    def handle_starttag(self, name, attrs, state, contentstate):
        if state.current_block is None:
            # ignore line breaks that exist at the top level
            return

        state.current_block.text += "\n"

    def handle_endtag(self, name, state, contentstate):
        pass


class HtmlToContentStateHandler(HTMLParser):
    def __init__(self, features=()):
        self.paragraph_handler = BlockElementHandler("unstyled")
        self.element_handlers = HTMLRuleset(
            {
                "p": self.paragraph_handler,
                "br": LineBreakHandler(),
            }
        )
        for feature in features:
            rule = feature_registry.get_converter_rule("contentstate", feature)
            if rule is not None:
                self.element_handlers.add_rules(rule["from_database_format"])

        super().__init__(convert_charrefs=True)

    def reset(self):
        self.state = HandlerState()
        self.contentstate = ContentState()

        # stack of (name, handler) tuples for the elements we're currently inside
        self.open_elements = []

        super().reset()

    def handle_starttag(self, name, attrs):
        attr_dict = dict(
            attrs
        )  # convert attrs from list of (name, value) tuples to a dict
        element_handler = self.element_handlers.match(name, attr_dict)

        if element_handler is None and not self.open_elements:
            # treat unrecognised top-level elements as paragraphs
            element_handler = self.paragraph_handler

        self.open_elements.append((name, element_handler))

        if element_handler:
            element_handler.handle_starttag(name, attrs, self.state, self.contentstate)

    def handle_endtag(self, name):
        if not self.open_elements:
            return  # avoid a pop from an empty list if we have an extra end tag
        expected_name, element_handler = self.open_elements.pop()
        assert name == expected_name, "Unmatched tags: expected {}, got {}".format(
            expected_name,
            name,
        )
        if element_handler:
            element_handler.handle_endtag(name, self.state, self.contentstate)

    def handle_data(self, content):
        # normalise whitespace sequences to a single space unless whitespace is contained in <pre> tag,
        # in which case, leave it alone
        # This is in line with https://www.w3.org/TR/html4/struct/text.html#h-9.1
        content = re.sub(WHITESPACE_RE, " ", content)

        if self.state.current_block is None:
            if content == " ":
                # ignore top-level whitespace
                return
            else:
                # create a new paragraph block for this content
                add_paragraph_block(self.state, self.contentstate)

        if content == " ":
            # if leading_whitespace = strip, this whitespace node is not significant
            #   and should be skipped.
            # For other cases, _don't_ output the whitespace yet, but set leading_whitespace = force
            # so that a space is forced before the next text node or inline element. If no such node
            # appears (= we reach the end of the block), the whitespace can rightfully be dropped.
            if self.state.leading_whitespace != STRIP_WHITESPACE:
                self.state.leading_whitespace = FORCE_WHITESPACE
        else:
            # strip or add leading whitespace according to the leading_whitespace flag
            if self.state.leading_whitespace == STRIP_WHITESPACE:
                content = content.lstrip()
            elif (
                self.state.leading_whitespace == FORCE_WHITESPACE
                and not content.startswith(" ")
            ):
                content = " " + content
            if content.endswith(" "):
                # don't output trailing whitespace yet, because we want to discard it if the end
                # of the block follows. Instead, we'll set leading_whitespace = force so that
                # any following text or inline element will be prefixed by a space
                content = content.rstrip()
                self.state.leading_whitespace = FORCE_WHITESPACE
            else:
                # no trailing whitespace here - any leading whitespace at the start of the
                # next text node should be respected
                self.state.leading_whitespace = KEEP_WHITESPACE

            self.state.current_block.text += content

    def close(self):
        # if content ends in an atomic block (or is empty), need to append a spacer paragraph
        if not self.state.has_preceding_nonatomic_block:
            add_paragraph_block(self.state, self.contentstate)
        super().close()
