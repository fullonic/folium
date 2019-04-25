from collections import OrderedDict
from branca.element import MacroElement, JavascriptLink, CssLink, Figure
from jinja2 import Template
from folium.utilities import parse_options
from ..map import Layer


class PanelLayer(MacroElement):
    _template = Template("""
        {% macro script(this,kwargs) %}
        function iconName(name) {
        	return '<i class="'+name+'"></i>';}

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
        {%- for key, layer, icon in this.overlayers_data %}
        { name: {{ key|tojson }},
        icon: iconName("{{ icon }}"),
        layer: {{layer}} },
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

    def __init__(self, group_name=None, group_collapsed=False,
                 icons=None, collapsibleGroups=True, collapsed=True, **kwargs):  # noqa
        super(PanelLayer, self).__init__()
        self._name = "PanelLayer"
        self.collapsed = True
        self.group_name = group_name or "Define a Group Name"
        self.options = parse_options(
            collapsed=collapsed,
            collapsibleGroups=collapsibleGroups,
            **kwargs)
        self.icons = icons
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
                print(item.get_name())
                self.overlayers[key] = item.get_name()
                if not item.show:
                    self.layers_untoggle[key] = item.get_name()
        self.overlayers_data = zip(self.overlayers.keys(),
                                   self.overlayers.values(),
                                   self.icons)
        super(PanelLayer, self).render()

        # Add CSS and JS files
        figure = self.get_root()
        assert isinstance(figure, Figure), ('You cannot render this Element '
                                            'if it is not in a Figure.')

        figure.header.add_child(CssLink("./static_files/leaflet-panel-layers.css"))
        figure.header.add_child(JavascriptLink("./static_files/leaflet-panel-layers.js"))
