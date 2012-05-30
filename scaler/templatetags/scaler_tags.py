import time

from django import template

register = template.Library()


@register.tag
def delay(parser, token):
    tag_name, value = token.split_contents()
    return DelayNode(value)


class DelayNode(template.Node):

    def __init__(self, value):
        self.value = template.Variable(value)

    def render(self, context):
        value = self.value.resolve(context)
        if value:
            time.sleep(float(value))
            return "Delayed by %s seconds" % value
