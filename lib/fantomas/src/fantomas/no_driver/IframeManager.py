def get_iframes_of_document(node):
    document_nodes = []
    if hasattr(node, 'content_document') and node.content_document is not None:
        if hasattr(node.content_document, 'node_name') and node.content_document.node_name == '#document':
            document_nodes.append(node.content_document)
        document_nodes.extend(get_iframes_of_document(node.content_document)) #type: ignore
    if hasattr(node, 'children') and node.children is not None:
        for child in node.children:
            document_nodes.extend(get_iframes_of_document(child)) #type: ignore
    return document_nodes
