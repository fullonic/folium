"""Panel layers plugin."""

from collections import OrderedDict

from branca.element import CssLink, Figure, JavascriptLink, MacroElement

from folium.utilities import parse_options

from jinja2 import Template

from ..map import Layer


class PanelLayer(MacroElement):
    """
    PanelLayer.

    Parameters
    ----------
    title: str, default None,
        Title of the control panel
    raster_group_name: str, default "Raster Layers"
        Name for the group of raster layers only.
    compact: bool, default True
        Controls panel size. If False, panel will have the height of the screen
    collapsed: bool, default False
        Panel collapsed at startup.
    collapsible_groups: bool, default True
        Groups of layers is collapsible by button
    icons: list, default None
        List of fontawesome icons to be show on left size of each layer name (only for data layers).
        Icons list length and data layers should be the same. Also, the order of each icon must be
        the same than the data layers in order to coincide each icon in the respective layer name.
    only_raster: bool. default False
        Makes possible create a layer panel with only raster (tiles) layers when set True.
    only_vector: bool. default False
        Makes possible create a layer panel with only vector (data) layers when set True.
        The same way, is possible to create two separate panel (see examples below)
    **kwargs
        Please see https://github.com/stefanocudini/leaflet-panel-layers/#options

    Examples
    --------
    Examples here

    """

    _template = Template("""
        {% macro script(this,kwargs) %}

        {% if this.only_vector %}
            var baseLayers = null;
        {% else %}
            var baseLayers = [{
                group: "{{ this.raster_group_name }}",
                icon: "{{ this.icon }}",
                collapsed: {{ this.collapsed|tojson }},
                layers: [
                {%- for key, val in this.base_layers.items() %}
                    {name: {{ key|tojson }},
                    layer: {{val}} },
            {%- endfor %}]}];{% endif %}
        {% if this.only_raster %}
            var overLayers = null;
        {% else %}
            var overLayers = [
                {% for g in this.overlayers_data %}
                    {"group": "{{ g["group"] }}",
                    "layers": [{% for v in g["layers"] %}
                    {"name": {{ v["name"]|tojson }},
                    "icon": {{ v["icon"]|tojson }},
                    "layer": {{ v["layer"] }} },
                    {% endfor %} ]},
                {% endfor %}
            ];

        {% endif %}


        var panelLayers = new L.Control.PanelLayers(
                baseLayers,
                overLayers,
                {{ this.options|tojson }});
            {{ this._parent.get_name() }}.addControl(panelLayers)

            {%- for val in this.layers_untoggle.values() %}
            {{ val }}.remove();
            {%- endfor %}
        {% endmacro %}
        """)

    def __init__(self, title=None, raster_group_name=None,
                 data_group_name=None,
                 collapsible_groups=True,
                 collapsed=True, icons=None,
                 only_raster=False, only_vector=False,
                 group_by=None,
                 **kwargs):  # noqa
        super(PanelLayer, self).__init__()
        self._name = 'PanelLayer'
        self.raster_group_name = raster_group_name or ' '
        self.data_group_name = data_group_name or ' '
        self.collapsed = collapsed
        self.options = parse_options(
            collapsed=self.collapsed,
            collapsible_groups=collapsible_groups,
            title=title,
            **kwargs)
        self.group_by = group_by or []

        self.icons = icons
        self.only_raster = only_raster
        self.only_vector = only_vector

        self.base_layers = OrderedDict()
        self.overlayers = OrderedDict()
        self.layers_untoggle = OrderedDict()

    def icon_name(self, name):
        return '<i class="' + name + '"></i>'

    def render(self, **kwargs):
        """Render the HTML representation of the element."""
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
        # simple panel
        if not self.group_by:
            g = {"group": self.data_group_name,
                 "layers": ""}
            data_layer = []
            layers = self.overlayers
            for name, layer in layers.items():
                data_layer.append({"name": name,
                                   "layer": layer})

            g["layers"] = data_layer
            self.overlayers_data = [g]

            # Deal with grouping layers in different panels
        else:
            assert len(self.group_by) == len(self.data_group_name), (
                "The length of group name list must be the same than the layer data group."
            )
            _group_layers = []
            for i, name in enumerate(self.data_group_name):
                _buffer = {"group": name,
                           "layers": []}
                icons = self.icons[i]
                layer_name = self.group_by[i]

                for i, layer in enumerate(layer_name):
                    d = {"name": layer,
                         "icon": self.icon_name(icons[i]),
                         "layer": self.overlayers[layer]}
                    _buffer["layers"].append(d)
                _group_layers.append(_buffer)
            # print(_group_layers)
            self.overlayers_data = _group_layers

        super(PanelLayer, self).render()

        # Add CSS and JS files
        figure = self.get_root()
        assert isinstance(figure, Figure), ('You cannot render this Element '
                                            'if it is not in a Figure.')

        figure.header.add_child(CssLink('./static_files/leaflet-panel-layers.css'))
        figure.header.add_child(JavascriptLink('./static_files/leaflet-panel-layers.js'))


# l = [("name", [1,2,3], ["red", "green", "blue"])]
# for i in l:
#     print(l[0][0])
#
