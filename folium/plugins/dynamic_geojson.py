from branca.element import Element, Figure, MacroElement
from jinja2 import Template


class DynamicGeoJson(MacroElement):
    """ GeoJson feature to consume live API data based on map bounds.

    Each time an event happen making the maps bound change, the four vertices of the map bounds will
    be saved in 4 variables: nW, nE, sE, sW. Using this 4 vertices, a API request can be made
    to provide geographic information that is present inside this map bound. This data is acquired
    by using leaflet .getBounds()
    ***Experimental***

    Parameters
    ----------
    action: str, default "moveend"
        What actions is need to performance in order to make a api call. For possible actions,
        See https://leafletjs.com/reference-1.4.0.html#map-zoomlevelschange
    url_root: str, default None
        The root of your api without the endpoint variables
        example: "https://api.somesource/apiv1/"
    url_pattern: str, default None
        This will be the endpoint pattern need to make the request, a python string but will be
        evaluate by javascript.
        See example bellow
    order: tuple, default ("lng", "lat")
        Order of the coordinates that present each point: ("lng", "lat") or ("lat", "lng")
    delimiter: str, default ","
        How lng and lat of each point is separated

    Examples
    --------
    # Create first the url:
    url_root = "https://api.somesource/apiv1/"
    # Will be allays 4 points available: nW, nE, sE, sW.
    # If all them are necessary and each joined by a '&', the pattern would be:
    url_pattern = "nW+'&'+nE+'&'+sE+'&'+sW"

    # Now we just need to create a new GeoJson layer and make it dynamically
    folium.GeoJson(geo_data, dynamic=folium.DynamicGeoJson(,
                       url_root=url_root,
                       url_pattern=url_pattern)).add_to(map)

    """
    _template = Template("""
    {% macro script(this, kwargs) %}

    // JS vars: Revision needed !!
    {% if this.live_update %}
    {{ this._parent.parent_map.get_name() }}.on("{{ this.action }}",
    {% else %}
    $( "#reload" ).click({% endif %} function() {
    // This will get all map bounds and make all 2 points coordinates available for later use in API
    // call

    d = "{{ this.delimiter }}";
    latlng={{ this._parent.parent_map.get_name() }}.getBounds();
    nW = latlng._southWest.{{ this.order[0] }} + d + latlng._northEast.{{ this.order[1] }}
    nE = latlng._northEast.{{ this.order[0] }} + d + latlng._northEast.{{ this.order[1] }}
    sE = latlng._northEast.{{ this.order[0] }} + d + latlng._southWest.{{ this.order[1] }}
    sW = latlng._southWest.{{ this.order[0] }} + d + latlng._southWest.{{ this.order[1] }}

    // This will make a new rest api call.
    var url = "{{ this.url_root }}" + {{ this.pattern }};
    $.ajax({url: url, dataType: 'json', async: true,
        success: function(data) {
        {{ this._parent.get_name() }}.clearLayers();
        {{ this._parent.get_name() }}.addData(data);
        {% if this._parent._parent.get_name()|truncate(14, True, "") == "marker_cluster" %}
        {{ this._parent._parent.get_name() }}.clearLayers();
        {{ this._parent.get_name() }}.addTo({{ this._parent._parent.get_name() }});
        {% endif %}
        }});
    });

    {% endmacro %}
    """)

    def __init__(self, action="moveend", url_root=None,
                 url_pattern=None, order=("lng", "lat"), delimiter=",",
                 live_update=False, button_text="Search this area"):
        super(DynamicGeoJson, self).__init__()
        self._name = "DynamicGeoJson"
        self.action = action
        self.url_root = url_root
        self.pattern = url_pattern
        self.order = order
        self.delimiter = delimiter
        self.live_update = live_update
        self.button_text = button_text

    def render(self, **kwargs):
        super(DynamicGeoJson, self).render(**kwargs)
        figure = self.get_root()
        assert isinstance(figure, Figure), ('You cannot render this Element '
                                            'if it is not in a Figure.')

        button_style = """
            <style>
                #reload {
                    position: absolute;
                    z-index: 999;
                    padding: 6px;
                    right: 48%;
                    font-size: 12px;
                    text-decoration: none;
                    top: 3%;
                }
            </style>
        """
        button_reload = """
        <button type="button" id="reload" class="btn btn-default btn-sm">{0}</button""".format(
            self.button_text)  # noqa

        if not self.live_update:
            figure.header.add_child(Element(button_style), name='reload')
            figure.html.add_child(Element(button_reload), name='button_reload')
