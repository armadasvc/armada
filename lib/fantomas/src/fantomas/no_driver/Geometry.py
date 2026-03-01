from nodriver import *
from .IframeManager import *

async def get_viewport_size(tab):
    dimensions = await tab.send(cdp.page.get_layout_metrics())
    dimension = dimensions[1]
    return [dimension.client_width, dimension.client_height]


async def get_coordinates_and_size(tab,selector_array):
    selector_css,ordinal = selector_array
    doc = await tab.send(cdp.dom.get_document(-1, True))
    page_node = doc.node_id
    targetted_elements_array = await tab.send(cdp.dom.query_selector_all(page_node,selector_css))
    await tab.send(cdp.emulation.set_page_scale_factor(1)) # Avoid box model errors
    targetted_element_box = await tab.send(cdp.dom.get_box_model(targetted_elements_array[ordinal]))
    x = int(targetted_element_box.content[0])
    y = int(targetted_element_box.content[1])
    width = int(targetted_element_box.width)
    height = int(targetted_element_box.height)
    return [x,y,width,height]


async def get_coordinates_and_size_in_iframe(tab,iframe_number,selector_array):
        selector_css, ordinal = selector_array
        document = await tab.send(cdp.dom.get_document(-1, True))
        iframes_array = get_iframes_of_document(document)
        iframe = iframes_array[iframe_number]
        iframe_node_id = iframe.node_id
        targetted_elements_array = await tab.send(cdp.dom.query_selector_all(iframe_node_id,selector_css))
        targetted_element_node_id = targetted_elements_array[ordinal]
        await tab.send(cdp.emulation.set_page_scale_factor(1)) # Avoid box model errors
        targetted_element_box = await tab.send(cdp.dom.get_box_model(targetted_element_node_id))
        x = int(targetted_element_box.content[0])
        y = int(targetted_element_box.content[1])
        width = int(targetted_element_box.width)
        height = int(targetted_element_box.height)
        return [x,y,width,height]