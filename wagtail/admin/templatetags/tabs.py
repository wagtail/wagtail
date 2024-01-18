from django import template

register = template.Library()


def generate_tab_panel_id(title):
    return f'tab-{title.lower().replace(" ",  "-")}'


def generate_tab_label_id(title):
    return f'tab-label-{title.lower().replace(" ",  "-")}'


@register.tag
def tabs(parser, token):
    # Parse tabs and content
    tabs = parser.parse(("endtabs",))
    parser.delete_first_token()
    return TabsNode(tabs, token)


class TabsNode(template.Node):
    def __init__(self, tabs, token):
        self.tabs = tabs
        self.token = token

    def render(self, context):
        output = f"""
          <div class="tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#loadTabsFromHistory" data-w-tabs-active-tab-id-value=""> 
          <div class="w-tabs__wrapper"> 
          <div class="w-tabs__list" role="tablist" data-w-tabs-target="tabList">
        """
        for node in self.tabs:
            if isinstance(node, TabNode):
                output += node.render(context)  # Render each tab's content
        output += """
          </div>
          </div>
        """
        output += """
          <div class="tab-content tab-content--comments-enabled" >
        """
        for node in self.tabs:
            if isinstance(node, TabNode):
                tab_title = node.kwargs.get("title").strip('"')
                tab_label_id = generate_tab_label_id(tab_title)
                tab_panel_id = generate_tab_panel_id(tab_title)

                output += f"""<section id={tab_panel_id} class="w-tabs__panel " role="tabpanel" aria-labelledby={tab_label_id} hidden="true" data-w-tabs-target="tabPanel">"""
                output += node.content.render(context)
                output += "</section>"

        output += """
          </div>
          </div>
        """
        return output


@register.tag
def tab(parser, token):
    args = token.split_contents()
    kwargs = {arg.split("=")[0]: arg.split("=")[1] for arg in args[1:]}
    content = parser.parse(("endtab",))
    parser.delete_first_token()
    return TabNode(kwargs, content)


class TabNode(template.Node):
    def __init__(self, kwargs, content):
        self.kwargs = kwargs
        self.content = content

    def render(self, context):
        tab_title = self.kwargs.get("title").strip('"')
        tab_label_id = generate_tab_label_id(tab_title)
        tab_panel_id = generate_tab_panel_id(tab_title)
        output = f"""<a id={tab_label_id} href="#{tab_panel_id}" class="w-tabs__tab" role="tab" data-action="click->w-tabs#changeTab keydown->w-tabs#switchTabOnArrowPress" aria-controls={tab_panel_id} data-w-tabs-target="tabLabel">{tab_title}</a>"""
        return output
