import xml.etree.ElementTree as ET
from pprint import pprint
import pydot
import re
import sys

# part of the code is taken from https://github.com/cole-st-john/yEdExtended/blob/master/src/yedextended/__init__.py


NS = {
    "graphml":"http://graphml.graphdrawing.org/xmlns" ,
    "java":"http://www.yworks.com/xml/yfiles-common/1.0/java" ,
    "sys":"http://www.yworks.com/xml/yfiles-common/markup/primitives/2.0" ,
    "x":"http://www.yworks.com/xml/yfiles-common/markup/2.0" ,
    "xsi":"http://www.w3.org/2001/XMLSchema-instance" ,
    "y":"http://www.yworks.com/xml/graphml" ,
    "yed":"http://www.yworks.com/xml/yed/3" ,
}

def check_color(color):
	if not (type(color) is str and re.match(r'^#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$',color)):
		print(f"type of color may not match: '{color}'",file=sys.stdout)
	return color
def add_style(where,item):
	if 'style' not in where:
		where['style'] = item
	else:
		where['style'] += (','+item)

def pydot_from_graphml(graph_str):
	'graph_str - filename or xml(graphml) string'
	if not graph_str.startswith('<?xml '):
	    with open(graph_str, "r") as graph_file:
	        graph_str = graph_file.read()
	root = ET.fromstring(graph_str)

	#all_keys = root.findall("graphml:key",NS)
	#key_dict = dict()
	#for a_key in all_keys:
	#	sub_key_dict = dict()
	#	key_id = a_key.attrib.get("id")
	#	# sub_key_dict["label"] = a_key.attrib.get("for")
	#	sub_key_dict["attr"] = a_key.attrib.get("attr.name", None)
	#	# sub_key_dict["label"] = a_key.attrib.get("type")
	#	key_dict[key_id] = sub_key_dict
	#print("key_dict:")
	#pprint(key_dict)

	## Get major graph node
	graph_root = root.find("graphml:graph",NS)
	## get major graph info
	assert graph_root.get("edgedefault")=="directed"
	assert graph_root.get("id")=="G"

	# instantiate graph object
	new_graph = pydot.Dot(graph_type="digraph")

	def is_group_node(node):
		return "foldertype" in node.attrib
	def check_not_none(x):
		assert x!=None
		return x

	def process_graph(parent, input_node):
		# Get sub nodes of this node (group or graph)
		current_level_nodes = input_node.findall("graphml:node",NS)
		current_level_edges = input_node.findall("graphml:edge",NS)

		for node in current_level_nodes:
			# normal nodes
			if not is_group_node(node):
				node_init_dict = dict()
				node_id = check_not_none(node.get('id',None))

				# <node id="n1">
				#existing_node_id = node.attrib.get("id", None)  # FIXME:

				data_nodes = node.findall("graphml:data",NS)
				info_node = None
				for data_node in data_nodes:
					info_node = data_node.find("y:GenericNode",NS) or data_node.find("y:ShapeNode",NS)
					if info_node is not None:
						#node_init_dict["node_type"] = info_node.tag

						# Geometry information
						node_geom = info_node.find("y:Geometry",NS)
						if node_geom is not None:
							# print(f"{node_geom.tag = }, {node_geom.get("x") =} {node_geom.get("y") =} ")
							node_init_dict['pos'] = node_geom.get('x')+','+str(-float(node_geom.get('y')))+'!'
							#geometry_vars = ["height", "width", "x", "y"]

						node_label = info_node.find("y:NodeLabel",NS)
						if node_label is not None:
							node_init_dict["label"] = node_label.text

							# TODO: PORT REST OF NODELABEL

						# <Fill color="#FFCC00" transparent="false" />
						fill = info_node.find("y:Fill",NS)
						if fill is not None:
							node_init_dict["fillcolor"] = check_color(fill.get("color"))
							add_style(node_init_dict,'filled')
							#node_init_dict["transparent"] = fill.get("transparent")

						# <BorderStyle color="#000000" type="line" width="1.0" />
						#border_style = info_node.find("y:BorderStyle",NS)
						#if border_style is not None:
						#	node_init_dict["border_color"] = border_style.get("color")
						#	node_init_dict["border_type"] = border_style.get("type")
						#	node_init_dict["border_width"] = border_style.get("width")

						# <Shape type="rectangle" />
						#shape_sub = info_node.find("y:Shape",NS)
						#if shape_sub is not None:
						#	node_init_dict["shape"] = shape_sub.get("type")

						#uml = info_node.find("y:UML",NS)
						#if uml is not None:
						#	node_init_dict["shape"] = uml.get("AttributeLabel")
						# TODO: THERE IS FURTHER DETAIL TO PARSE HERE under uml
					#else:
					#	info = data_node.text
					#	if info is not None:
					#		info = info.replace("<![CDATA[", "").replace("]]>", "")  # unneeded schema
					#
					#		the_key = data_node.attrib.get("key")

					#		info_type = key_dict[the_key]["attr"]
					#		if info_type in ["url", "description"]:
					#			node_init_dict[info_type] = info
				# Removing empty items
				node_init_dict = {key: value for (key, value) in node_init_dict.items() if value is not None}
				# create node
				parent.add_node(pydot.Node(node_id,**node_init_dict))

		# edges then establish connections
		for edge_node in current_level_edges:
			edge_init_dict = dict()

			# <node id="n1">
			edge_init_dict['id'] = edge_node.attrib.get("id", None)
			source = edge_node.get("source")
			target = edge_node.get("target")

			# <data key="d5">
			data_nodes = edge_node.findall("graphml:data",NS)
			for data_node in data_nodes:
				polylineedge = data_node.find("y:PolyLineEdge",NS)

				if polylineedge is not None:
					# TODO: ADD POSITION MANAGEMENT
					# path_node = polylineedge.find("y:Path",NS)
					# if path_node:
					#   edge_init_dict["label"] = path_node.attrib.get("sx")
					#   edge_init_dict["label"] = path_node.attrib.get("sy")
					#   edge_init_dict["label"] = path_node.attrib.get("tx")
					#   edge_init_dict["label"] = path_node.attrib.get("ty")

					linestyle_node = polylineedge.find("y:LineStyle",NS)
					if linestyle_node is not None:
						edge_init_dict["color"] = linestyle_node.attrib.get("color", None)
					#	edge_init_dict["line_type"] = linestyle_node.attrib.get("type", None)
					#	edge_init_dict["width"] = linestyle_node.attrib.get("width", None)

					#arrows_node = polylineedge.find("y:Arrows",NS)
					#if arrows_node is not None:
					#	edge_init_dict["arrowfoot"] = arrows_node.attrib.get("source", None)
					#	edge_init_dict["arrowhead"] = arrows_node.attrib.get("target", None)

					edgelabel_node = polylineedge.find("y:EdgeLabel",NS) # todo: many labels
					if edgelabel_node is not None:
						edge_init_dict["label"] = edgelabel_node.text

				#else:
				#	info = data_node.text
				#	if info is not None:
				#		info = re.sub(r"<!\[CDATA\[", "", info)  # unneeded schema
				#		info = re.sub(r"\]\]>", "", info)  # unneeded schema

				#		the_key = data_node.attrib.get("key")

				#		info_type = key_dict[the_key]["attr"]
				#		if info_type in ["url", "description"]:
				#			edge_init_dict[info_type] = info

			# bendstyle_node = not_implemented_element(polylineedge.find("y:BendStyle",NS))
			# edge_init_dict["smoothed"] = linestyle_node.attrib.get("smoothed") # TODO: ADD THIS

			# TODO:
			#   CUSTOM PROPERTIES

			# Removing empty items
			edge_init_dict = {key: value for (key, value) in edge_init_dict.items() if value is not None}
			parent.add_edge(pydot.Edge(source,target,**edge_init_dict))

	process_graph(parent=new_graph, input_node=graph_root)

	return new_graph

def pydot_to_graphml(G,filename=None):
	"""
	If filename is not None - save to file
	else return .graphml string
	"""

	# Creating XML structure in Graphml format
	# xml = ET.Element("?xml", version="1.0", encoding="UTF-8", standalone="no")

	graphml = ET.Element("graphml", xmlns="http://graphml.graphdrawing.org/xmlns")
	graphml.set("xmlns:java", "http://www.yworks.com/xml/yfiles-common/1.0/java")
	graphml.set("xmlns:sys", "http://www.yworks.com/xml/yfiles-common/markup/primitives/2.0")
	graphml.set("xmlns:x", "http://www.yworks.com/xml/yfiles-common/markup/2.0")
	graphml.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
	graphml.set("xmlns:y", "http://www.yworks.com/xml/graphml")
	graphml.set("xmlns:yed", "http://www.yworks.com/xml/yed/3")
	graphml.set(
		"xsi:schemaLocation",
		"http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd",
	)

	# Adding some implementation specific keys for identifying urls, descriptions
	node_key = ET.SubElement(graphml, "key", id="data_node")
	node_key.set("for", "node")
	node_key.set("yfiles.type", "nodegraphics")

	# Definition: url for Node
	node_key = ET.SubElement(graphml, "key", id="url_node")
	node_key.set("for", "node")
	node_key.set("attr.name", "url")
	node_key.set("attr.type", "string")

	# Definition: description for Node
	node_key = ET.SubElement(graphml, "key", id="description_node")
	node_key.set("for", "node")
	node_key.set("attr.name", "description")
	node_key.set("attr.type", "string")

	# Definition: url for Edge
	node_key = ET.SubElement(graphml, "key", id="url_edge")
	node_key.set("for", "edge")
	node_key.set("attr.name", "url")
	node_key.set("attr.type", "string")

	# Definition: description for Edge
	node_key = ET.SubElement(graphml, "key", id="description_edge")
	node_key.set("for", "edge")
	node_key.set("attr.name", "description")
	node_key.set("attr.type", "string")

	# Definition: Custom Properties for Nodes and Edges
	#for prop in self.custom_properties:
	#	graphml.append(prop.convert_to_xml())

	edge_key = ET.SubElement(graphml, "key", id="data_edge")
	edge_key.set("for", "edge")
	edge_key.set("yfiles.type", "edgegraphics")

	# Graph node containing actual objects
	graph = ET.SubElement(graphml, "graph", edgedefault="directed", id="G")
						  #edgedefault=self.directed, id=self.id)

	# Convert python graph objects into xml structure
	for node in G.get_nodes():
		#"""Converting node object to xml object"""

		xml_node = ET.Element("node", id=node.get_name())
		data = ET.SubElement(xml_node, "data", key="data_node")
		shape = ET.SubElement(data, "y:ShapeNode") # ... GenericNode

		if pos:=node.get("pos"):
			x,y = pos.replace('"','').replace('!','').split(',')
			ET.SubElement(shape, "y:Geometry", x=x, y=str(-float(y)))
		# <y:Geometry height="30.0" width="30.0" x="475.0" y="727.0"/>

		if (color:=node.get("fillcolor")) and node.get('style') and 'filled' in node.get('style'):
			ET.SubElement(shape, "y:Fill", color=check_color(color))
		#, transparent=self.transparent)

		#ET.SubElement(
		#    shape,
		#    "y:BorderStyle",
		#    color=self.border_color,
		#    type=self.border_type,
		#    width=self.border_width,
		#)

		#for label in self.list_of_labels:
		#	label.addSubElement(shape)
		if label_text:=node.get("label"):
			NodeLabel = ET.SubElement(shape, "y:NodeLabel")
			NodeLabel.text = label_text


		#ET.SubElement(shape, "y:Shape", type=self.shape)

		# UML specific
		#if self.UML:
		#    UML = ET.SubElement(shape, "y:UML")

		#	attributes = ET.SubElement(UML, "y:AttributeLabel", type=self.shape)
		#	attributes.text = self.UML["attributes"]

		#	methods = ET.SubElement(UML, "y:MethodLabel", type=self.shape)
		#	methods.text = self.UML["methods"]

		#	stereotype = self.UML["stereotype"] if "stereotype" in self.UML else ""
		#	UML.set("stereotype", stereotype)

		# Special items
		#if self.url:
		#	url_node = ET.SubElement(xml_node, "data", key="url_node")
		#	url_node.text = self.url

		#if self.description:
		#	description_node = ET.SubElement(xml_node, "data", key="description_node")
		#	description_node.text = self.description

		# Node Custom Properties
		#for name, definition in Node.custom_properties_defs.items():
		#	node_custom_prop = ET.SubElement(xml_node, "data", key=definition.id)
		#	node_custom_prop.text = getattr(self, name)
		graph.append(xml_node)

	#for group in self.groups.values():
	#	graph.append(group.convert_to_xml())

	for edge in G.get_edges():
		#print("Откуда -> Куда:", edge.get_source(), "->", edge.get_destination())
		#print("Атрибуты:", edge.get_attributes())
		#print("label =", edge.get("label"))
		#graph.append(edge.convert_to_xml())
		#"""Converting edge object to xml object"""

		xml_edge = ET.Element(
			"edge",
			id=str(edge.get('id')),
			source=str(edge.get_source()),
			target=str(edge.get_destination()),
		)

		data = ET.SubElement(xml_edge, "data", key="data_edge")
		pl = ET.SubElement(data, "y:PolyLineEdge")

		ET.SubElement(pl, "y:Arrows", source="none", target="standard") # check graph/digraph
					  #source=self.arrowfoot, target=self.arrowhead)
		ET.SubElement(pl, "y:LineStyle", color=check_color(edge.get('color')))
			#, type=self.line_type, width=self.width)

		#for label in self.list_of_labels:
		#	label.addSubElement(pl)
		if label_text:=edge.get("label"):
			EdgeLabel = ET.SubElement(pl, "y:EdgeLabel")
			EdgeLabel.text = label_text

		#if self.url:
		#	url_edge = ET.SubElement(xml_edge, "data", key="url_edge")
		#	url_edge.text = self.url

		#if self.description:
		#	description_edge = ET.SubElement(xml_edge, "data", key="description_edge")
		#	description_edge.text = self.description

		# Edge Custom Properties
		#for name, definition in Edge.custom_properties_defs.items():
		#	edge_custom_prop = ET.SubElement(xml_edge, "data", key=definition.id)
		#	edge_custom_prop.text = getattr(self, name)

		graph.append(xml_edge)

	if filename is not None:
		tree = ET.ElementTree(graphml)
		with open(filename, "w", encoding="utf-8") as f:
		    tree.write(f, encoding="unicode", xml_declaration=True)
	else:
		ET.indent(graphml, space="  ", level=0)
		return ET.tostring(graphml, encoding="unicode")
