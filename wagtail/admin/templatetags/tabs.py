from django import template

register = template.Library()


@register.tag
def tabs(parser, token):
    # Parse tabs and content
    tabs = parser.parse(("endtabs",))
    args = token.split_contents()
    kwargs = {arg.split("=")[0]: arg.split("=")[1] for arg in args[1:]}
    parser.delete_first_token()
    return TabsNode(tabs, token, kwargs)


class TabsNode(template.Node):
    def __init__(self, tabs, token, kwargs):
        self.tabs = tabs
        self.token = token
        self.kwargs = kwargs

    def render(self, context):
        output = f"""
          <div class="tabs" data-controller="w-tabs" data-action="popstate@window->w-tabs#loadTabsFromHistory" data-w-tabs-active-tab-id-value={self.kwargs.get("active_tab_id")}> 
          <div class="w-tabs__wrapper"> 
          <div class="w-tabs__list" role="tablist">
        """
        for node in self.tabs:
            if isinstance(node, TabNode):
                output += node.render(
                    context, active_tab_id=self.kwargs.get("active_tab_id")
                )  # Render each tab's content
        output += """
          </div>
          </div>
        """
        output += """
          <div class="tab-content tab-content--comments-enabled" >
        """
        for node in self.tabs:
            if isinstance(node, TabNode):
                tab_label = node.kwargs.get("tab_id")
                tab_panel_id = tab_label.replace("-label", "")

                is_hidden = (
                    'hidden="true"'
                    if self.kwargs.get("active_tab_id") != tab_label
                    else ""
                )

                output += f"""<section id={tab_panel_id} class="w-tabs__panel " role="tabpanel" aria-labelledby={tab_label} {is_hidden}>"""
                output += node.content.render(context)  # Render each tab's content
                output += "</section>"

        output += """
          </div>
          </div>
        """
        return output


@register.tag
def tab(parser, token):
    # Parse tab attributes and content
    args = token.split_contents()
    kwargs = {arg.split("=")[0]: arg.split("=")[1] for arg in args[1:]}
    content = parser.parse(("endtab",))
    parser.delete_first_token()
    return TabNode(kwargs, content)


class TabNode(template.Node):
    def __init__(self, kwargs, content):
        self.kwargs = kwargs
        self.content = content

    def render(self, context, active_tab_id):
        tab_id = self.kwargs.get("tab_id")
        tab_id_panel = self.kwargs.get("tab_id").replace("-label", "").strip('"')
        tab_title = self.kwargs.get("title").strip('"')
        tab_selected = (
            'aria-selected="true"' if active_tab_id == self.kwargs.get("tab_id") else ""
        )
        output = f"""<a id={tab_id} href="#{tab_id_panel}" class="w-tabs__tab" role="tab" data-action="click->w-tabs#changeTab keydown->w-tabs#switchTabOnArrowPress keydown->w-tabs#switchTabOnArrowPress" {tab_selected} aria-controls={tab_id}>{tab_title}</a>"""
        return output
