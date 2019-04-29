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
        function iconName(name) {
            return '<i class="'+name+'"></i>';}
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
            var overLayers = [{
            group: "{{this.data_group_name}}",
            layers:[
            {%- for key, layer, icon in this.overlayers_data %}
                { name: {{ key|tojson }},
                icon: iconName("{{ icon }}"),
                layer: {{layer}} },
            {%- endfor %}]}]; {% endif %}
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
        self.group_by = group_by

        self.icons = icons
        self.only_raster = only_raster
        self.only_vector = only_vector

        self.base_layers = OrderedDict()
        self.overlayers = OrderedDict()
        self.layers_untoggle = OrderedDict()

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

        self.overlayers_data = zip(self.overlayers.keys(),
                                   self.overlayers.values(),
                                   self.icons if self.icons else self.overlayers.keys())
        # Deal with grouping layers in different panels
        data_layer = []
        if self.group_by:
            i = 0
            for name, layer in self.overlayers.items():
                if name in self.group_by:
                    data_layer.append((name, layer, self.icons[i] if self.icons else None))
                    i += 1
            self.overlayers_data = data_layer

        super(PanelLayer, self).render()

        # Add CSS and JS files
        figure = self.get_root()
        assert isinstance(figure, Figure), ('You cannot render this Element '
                                            'if it is not in a Figure.')

        figure.header.add_child(CssLink('./static_files/leaflet-panel-layers.css'))
        figure.header.add_child(JavascriptLink('./static_files/leaflet-panel-layers.js'))
