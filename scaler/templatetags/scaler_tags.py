import time

from django import template

register = template.Library()


@register.tag
def delay(parser, token):
    tag_name, value = token.split_contents()
    return DelayNode()


class DelayNode(template.Node):

    def render(self, context):
        value = float(context['request'].GET.get('delay', 0))
        if value:
            time.sleep(value)
            return "Delayed by %s seconds" % value
        return ''
