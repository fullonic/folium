from collections import OrderedDict
from branca.element import MacroElement, JavascriptLink, CssLink, Figure
from jinja2 import Template
from folium.utilities import parse_options
from ..map import Layer


class PanelLayer(MacroElement):
    _template = Template("""
        {% macro script(this,kwargs) %}
        var baseLayers = [{
            group: "{{ this.group_name }}",
            icon: "{{ this.icon }}",
            collapsed: {{ this.collapsed|tojson }},
            layers: [
            {%- for key, val in this.base_layers.items() %}
            {name: {{ key|tojson }},
            layer: {{val}} },
            {%- endfor %}
            ]
        }];

        var overLayers = [
        {%- for key, val in this.overlayers.items() %}
        { name: {{ key|tojson }},
        layer: {{val}} },
        {%- endfor %}
        ];

        var panelLayers = new L.Control.PanelLayers(
                baseLayers,
                overLayers,
                {{ this.options|tojson }}
            );
            {{ this._parent.get_name() }}.addControl(panelLayers)

            {%- for val in this.layers_untoggle.values() %}
            {{ val }}.remove();
            {%- endfor %}
        {% endmacro %}
        """)

    def __init__(self, group_name=None, collapsibleGroups=True, collapsed=True, **kwargs):  # noqa
        super(PanelLayer, self).__init__()
        self._name = "PanelLayer"
        self.collapsed = True
        self.group_name = group_name or "Define a Group Name"
        self.options = parse_options(
            collapsed=collapsed,
            collapsibleGroups=collapsibleGroups,
            **kwargs)
        self.base_layers = OrderedDict()
        self.overlayers = OrderedDict()
        self.layers_untoggle = OrderedDict()

    def render(self, **kwargs):
        """Renders the HTML representation of the element."""
        for item in self._parent._children.values():
            if not isinstance(item, Layer) or not item.control:
                continue
            key = item.layer_name
            if not item.overlay:
                self.base_layers[key] = item.get_name()
                if len(self.base_layers) > 1:
                    self.layers_untoggle[key] = item.get_name()
            else:
                self.overlayers[key] = item.get_name()
                if not item.show:
                    self.layers_untoggle[key] = item.get_name()
        super(PanelLayer, self).render()
        figure = self.get_root()
        assert isinstance(figure, Figure), ('You cannot render this Element '
                                            'if it is not in a Figure.')
        figure.header.add_child(CssLink("leaflet-panel-layers.css"))
        figure.header.add_child(JavascriptLink("leaflet-panel-layers.js"))
