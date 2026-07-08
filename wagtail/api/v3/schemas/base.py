from ninja import Schema


class ContentTypeSummarySchema(Schema):
    name: str
    label: str
