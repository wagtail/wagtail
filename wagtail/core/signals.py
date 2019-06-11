from django.dispatch import Signal

page_published = Signal(providing_args=['instance', 'revision'])
page_unpublished = Signal(providing_args=['instance'])
pre_page_move = Signal(providing_args=['instance', 'parent_page_before', 'parent_page_after', 'url_path_before', 'url_path_after'])
post_page_move = Signal(providing_args=['instance', 'parent_page_before', 'parent_page_after', 'url_path_before', 'url_path_after'])
