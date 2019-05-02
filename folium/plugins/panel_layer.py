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
                 prefix="fa", color="black",
                 only_raster=False, only_vector=False,
                 group_by=None,
                 **kwargs):  # noqa
        super(PanelLayer, self).__init__()
        self._name = 'PanelLayer'
        self.raster_group_name = raster_group_name or ' '
        self.data_group_name = data_group_name or ' '
        self.collapsed = collapsed
        self.options = parse_options(
            collapsed=collapsed,
            collapsible_groups=collapsible_groups,
            title=title,
            **kwargs)
        if not group_by:
            self.group_by = []
        else:
            # Check if group_by is a list or a list of lists. This allows to pass a single list of
            # layers to group_by in case of a single panel with only one group of data layers
            self.group_by = group_by if isinstance(group_by[0], list) else [group_by]
        self.icons = icons
        self.color = color
        self.prefix = prefix
        self.only_raster = only_raster
        self.only_vector = only_vector

        self.base_layers = OrderedDict()
        self.overlayers = OrderedDict()
        self.layers_untoggle = OrderedDict()

    def _icon_name(self, name):
        """Return the html representation of icon name."""
        _color = self.color
        return '<i class="' + self.prefix + " " + name + '" style="color:{};"></i>'.format(_color)

    def _check_icons(self, icons, layers, index=-1):
        """Calculate the size of icons list.

        Checks if the number of layers and the icons names provided for each group or panel
        are the same.
        """
        if icons is None:
            return ["None ", ] * len(layers)
        elif index == -1:
            _diff = len(icons) < len(layers)
            if bool(_diff):
                icons.append("None " * _diff)
                return icons
            else:
                return icons
        elif isinstance(icons[0], list):
            # checks if is a list of lists
            try:
                return icons[index]
            except IndexError:
                return ["None "] * len(layers)
        else:
            raise """There is a problem:
            You are doing something that hasn't expected. Check documentation"""

    def _create_layer(self, layer, icon):
        return {"name": layer,
                "icon": self._icon_name(icon),
                "layer": self.overlayers[layer]}

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
        # Simple panel: One panel, no groups
        if not self.group_by:
            _group = {"group": self.data_group_name,
                      "layers": ""}
            _data_layers = []
            icons = self._check_icons(self.icons, self.overlayers)
            for name, icon in zip(self.overlayers, icons):
                _data_layers.append(self._create_layer(name, icon))

            _group["layers"] = _data_layers
            self.overlayers_data = [_group]

        # Multiple panel with or without groups and single panel with groups
        else:
            assert len(self.group_by) == len(self.data_group_name), (
                "The length of group name list must be the same than the layer data group."
            )
            _group_layers = []
            for group, name in enumerate(self.data_group_name):
                _buffer = {"group": name,
                           "layers": []}
                layer_name = self.group_by[group]
                _icons = self._check_icons(self.icons, layer_name, group)

                for name, icon in zip(layer_name, _icons):
                    # Flag to check if icons names are a group of list or a single list
                    # Group of lists if used when a single panel is created with multiple groups
                    _buffer["layers"].append(self._create_layer(name, icon))
                _group_layers.append(_buffer)
            self.overlayers_data = _group_layers

        super(PanelLayer, self).render()

        # Add CSS and JS files
        figure = self.get_root()
        assert isinstance(figure, Figure), ('You cannot render this Element '
                                            'if it is not in a Figure.')

        figure.header.add_child(
            CssLink('../static_files/leaflet-panel-layers.css'))  # noqa
        figure.header.add_child(
            JavascriptLink('../static_files/leaflet-panel-layers.js'))  # noqa
