import re


class VariantNotImplemented(BaseException):
    pass


def symfem_format(string, params):
    out = f"\"{string}\""
    for p, v in params.items():
        if p == "variant":
            out += f", {p}=\"{v}\""
    return out


def basix_format(string, params):
    out = f"basix.ElementFamily.{string}"
    for p, v in params.items():
        out += f", {p}="
        if p == "lagrange_variant":
            out += f"basix.LagrangeVariant.{v}"
        elif p == "dpc_variant":
            out += f"basix.DPCVariant.{v}"
        elif p == "discontinuous":
            out += v
    return out


def basix_ufl_format(string, params):
    out = basix_format(string, {i: j for i, j in params.items() if i != "shape"})
    if "shape" in params:
        out += f", shape={params['shape']}"
    return out


def string_format(string, params):
    return f"\"{string}\""


def fiat_format(string, params):
    out = f"FIAT.{string}"
    started = False
    for p, v in params.items():
        if p == "variant":
            if not started:
                out += "(..."
                started = True
            out += f", {p}=\"{v}\""
    if started:
        out += ")"
    return out


def _parse_value(v):
    v = v.strip()
    if v[0] == "[" and v[-1] == "]":
        return [_parse_value(i) for i in v[1:-1].split(";")]
    if re.match(r"[0-9]+$", v):
        return int(v)
    return v


def parse_example(e):
    if " {" in e:
        e, rest = e.split(" {")
        rest = rest.split("}")[0]
        while re.search(r"\[([^\]]*),", rest):
            rest = re.sub(r"\[([^\]]*),", r"[\1;", rest)
        kwargs = {}
        for i in rest.split(","):
            key, value = i.split("=")
            kwargs[key] = _parse_value(value)
    else:
        kwargs = {}
    s = e.split(",")
    if len(s) == 3:
        ref, order, variant = s
    else:
        ref, order = e.split(",")
        variant = None
    return ref, int(order), variant, kwargs


def symfem_example(element):
    out = "import symfem"
    for e in element.examples:
        ref, ord, variant, kwargs = parse_example(e)
        ord = int(ord)

        symfem_name, params = element.get_implementation_string("symfem", ref, variant)

        if symfem_name is not None:
            out += "\n\n"
            out += f"# Create {element.name_with_variant(variant)} order {ord} on a {ref}\n"
            if ref == "dual polygon":
                out += f"element = symfem.create_element(\"{ref}(4)\","
            else:
                out += f"element = symfem.create_element(\"{ref}\","
            if "variant" in params:
                out += f" \"{symfem_name}\", {ord}, variant=\"{params['variant']}\""
            else:
                out += f" \"{symfem_name}\", {ord}"
            for i, j in kwargs.items():
                if isinstance(j, str):
                    out += f", {i}=\"{j}\""
                else:
                    out += f", {i}={j}"
            out += ")"
    return out


def basix_example(element):
    out = "import basix"
    for e in element.examples:
        ref, ord, variant, kwargs = parse_example(e)
        assert len(kwargs) == 0
        ord = int(ord)

        try:
            basix_name, params = element.get_implementation_string("basix", ref, variant)
        except VariantNotImplemented:
            continue

        if basix_name is not None:
            out += "\n\n"
            out += f"# Create {element.name_with_variant(variant)} order {ord} on a {ref}\n"
            out += "element = basix.create_element("
            out += f"basix.ElementFamily.{basix_name}, basix.CellType.{ref}, {ord}"
            if "lagrange_variant" in params:
                out += f", lagrange_variant=basix.LagrangeVariant.{params['lagrange_variant']}"
            if "dpc_variant" in params:
                out += f", dpc_variant=basix.DPCVariant.{params['dpc_variant']}"
            if "discontinuous" in params:
                assert params["discontinuous"] in ["True", "False"]
                out += f", discontinuous={params['discontinuous']}"
            out += ")"
    return out


def basix_ufl_example(element):
    out = "import basix\nimport basix.ufl"
    for e in element.examples:
        ref, ord, variant, kwargs = parse_example(e)
        assert len(kwargs) == 0
        ord = int(ord)

        try:
            basix_name, params = element.get_implementation_string("basix.ufl", ref, variant)
        except VariantNotImplemented:
            continue

        if basix_name is not None:
            out += "\n\n"
            out += f"# Create {element.name_with_variant(variant)} order {ord} on a {ref}\n"
            out += "element = basix.ufl.element("
            out += f"basix.ElementFamily.{basix_name}, basix.CellType.{ref}, {ord}"
            if "lagrange_variant" in params:
                out += f", lagrange_variant=basix.LagrangeVariant.{params['lagrange_variant']}"
            if "dpc_variant" in params:
                out += f", dpc_variant=basix.DPCVariant.{params['dpc_variant']}"
            if "discontinuous" in params:
                assert params["discontinuous"] in ["True", "False"]
                out += f", discontinuous={params['discontinuous']}"
            if "shape" in params:
                if ref == "interval":
                    dim = 1
                elif ref in ["triangle", "quadrilateral"]:
                    dim = 2
                else:
                    dim = 3
                out += ", shape=" + params["shape"].replace("dim", f"{dim}")
            out += ")"
    return out


def ufl_legacy_example(element):
    out = "import ufl_legacy"
    for e in element.examples:
        ref, ord, variant, kwargs = parse_example(e)
        assert len(kwargs) == 0
        ord = int(ord)

        try:
            ufl_name, params = element.get_implementation_string("ufl", ref, variant)
        except VariantNotImplemented:
            continue

        if ufl_name is not None:
            out += "\n\n"
            out += f"# Create {element.name_with_variant(variant)} order {ord} on a {ref}\n"
            if "type" in params:
                out += f"element = ufl_legacy.{params['type']}("
            else:
                out += "element = ufl_legacy.FiniteElement("
            out += f"\"{ufl_name}\", \"{ref}\", {ord})"
    return out


def bempp_example(element):
    out = "import bempp.api"
    out += "\n"
    out += "grid = bempp.api.shapes.regular_sphere(1)"
    for e in element.examples:
        ref, ord, variant, kwargs = parse_example(e)
        assert len(kwargs) == 0
        ord = int(ord)

        try:
            bempp_name, params = element.get_implementation_string("bempp", ref, variant)
        except VariantNotImplemented:
            continue

        if bempp_name is None:
            continue
        orders = [int(i) for i in params["orders"].split(",")]

        if ord in orders:
            out += "\n\n"
            out += f"# Create {element.name} order {ord}\n"
            out += "element = bempp.api.function_space(grid, "
            out += f"\"{bempp_name}\", {ord})"
    return out


def fiat_example(element):
    out = "import FIAT"
    for e in element.examples:
        ref, ord, variant, kwargs = parse_example(e)
        assert len(kwargs) == 0
        ord = int(ord)

        try:
            fiat_name, params = element.get_implementation_string("fiat", ref, variant)
        except VariantNotImplemented:
            continue

        if fiat_name is None:
            continue

        if "order" in params and params["order"] != "None" and ord != int(params["order"]):
            continue

        out += "\n\n"
        out += f"# Create {element.name_with_variant(variant)} order {ord}\n"
        if ref in ["interval", "triangle", "tetrahedron"]:
            cell = f"FIAT.ufc_cell(\"{ref}\")"
        elif ref == "quadrilateral":
            cell = "FIAT.reference_element.UFCQuadrilateral()"
        elif ref == "hexahedron":
            cell = "FIAT.reference_element.UFCHexahedron()"
        else:
            raise ValueError(f"Unsupported cell: {ref}")
        out += f"element = FIAT.{fiat_name}({cell}"
        if "order" not in params or params["order"] != "None":
            out += f", {ord}"
        for i, j in params.items():
            if i != "order":
                out += f", {i}=\"{j}\""
        out += ")"
    return out


def to_array(data):
    import numpy as np

    if isinstance(data, (list, tuple)):
        return np.array([to_array(i) for i in data])
    return float(data)


def symfem_create_element(element, example):
    import symfem

    ref, ord, variant, kwargs = parse_example(example)
    ord = int(ord)
    symfem_name, params = element.get_implementation_string("symfem", ref, variant)
    assert symfem_name is not None
    if ref == "dual polygon":
        ref += "(4)"
    return symfem.create_element(ref, symfem_name, ord, **params)


class CachedSymfemTabulator:
    def __init__(self, element):
        self.element = element
        self.tables = []

    def tabulate(self, points):
        import numpy as np

        for i, j in self.tables:
            if i.shape == points.shape and np.allclose(i, points):
                return j
        shape = (points.shape[0], self.element.range_dim, self.element.space_dim)
        table = to_array(self.element.tabulate_basis(points, "xx,yy,zz")).reshape(shape)
        self.tables.append((points, table))
        return table


def symfem_verify(element, example):
    import symfem

    ref, ord, variant, kwargs = parse_example(example)
    ord = int(ord)
    symfem_name, params = element.get_implementation_string("symfem", ref, variant)
    assert symfem_name is not None
    if ref == "dual polygon":
        ref += "(4)"
    e = symfem.create_element(ref, symfem_name, ord, **params)
    edofs = [[e.entity_dofs(i, j) for j in range(e.reference.sub_entity_count(i))]
             for i in range(e.reference.tdim + 1)]
    t = CachedSymfemTabulator(e)
    return edofs, lambda points: t.tabulate(points)


def basix_verify(element, example):
    import basix

    ref, ord, variant, kwargs = parse_example(example)
    assert len(kwargs) == 0
    ord = int(ord)
    try:
        basix_name, params = element.get_implementation_string("basix", ref, variant)
    except VariantNotImplemented:
        raise NotImplementedError()
    if basix_name is None:
        raise NotImplementedError()
    kwargs = {}
    if "lagrange_variant" in params:
        kwargs["lagrange_variant"] = getattr(basix.LagrangeVariant, params['lagrange_variant'])
    if "dpc_variant" in params:
        kwargs["dpc_variant"] = getattr(basix.DPCVariant, params['dpc_variant'])
    if "discontinuous" in params:
        kwargs["discontinuous"] = params["discontinuous"] == "True"

    e = basix.create_element(
        getattr(basix.ElementFamily, basix_name), getattr(basix.CellType, ref), ord,
        **kwargs)
    return e.entity_dofs, lambda points: e.tabulate(0, points)[0].transpose((0, 2, 1))


def basix_ufl_verify(element, example):
    import basix
    import basix.ufl

    ref, ord, variant, kwargs = parse_example(example)
    assert len(kwargs) == 0
    ord = int(ord)
    try:
        basix_name, params = element.get_implementation_string("basix.ufl", ref, variant)
    except VariantNotImplemented:
        raise NotImplementedError()
    if basix_name is None:
        raise NotImplementedError()
    kwargs = {}
    if "lagrange_variant" in params:
        kwargs["lagrange_variant"] = getattr(basix.LagrangeVariant, params['lagrange_variant'])
    if "dpc_variant" in params:
        kwargs["dpc_variant"] = getattr(basix.DPCVariant, params['dpc_variant'])
    if "discontinuous" in params:
        kwargs["discontinuous"] = params["discontinuous"] == "True"
    if "shape" in params:
        if ref == "interval":
            dim = 1
        elif ref in ["triangle", "quadrilateral"]:
            dim = 2
        else:
            dim = 3
        kwargs["shape"] = tuple(
            dim if i == "dim" else int(i) for i in params["shape"][1:-1].split(",") if i != "")

    e = basix.ufl.element(
        getattr(basix.ElementFamily, basix_name), getattr(basix.CellType, ref), ord, **kwargs)
    return e.entity_dofs, lambda points: e.tabulate(0, points)[0].reshape(
        points.shape[0], e.value_size, -1)


def fiat_verify(element, example):
    import FIAT

    ref, ord, variant, kwargs = parse_example(example)
    assert len(kwargs) == 0
    ord = int(ord)
    try:
        fiat_name, params = element.get_implementation_string("fiat", ref, variant)
    except VariantNotImplemented:
        raise NotImplementedError()
    if fiat_name is None:
        raise NotImplementedError()
    if ref in ["interval", "triangle", "tetrahedron"]:
        cell = FIAT.ufc_cell(ref)
    elif ref == "quadrilateral":
        cell = FIAT.reference_element.UFCQuadrilateral()
    elif ref == "hexahedron":
        cell = FIAT.reference_element.UFCHexahedron()
    else:
        raise ValueError(f"Unsupported cell: {ref}")

    args = []
    if "order" in params:
        if params["order"] != "None":
            if ord != int(params['order']):
                raise NotImplementedError
            args.append(ord)
    else:
        args.append(ord)

    e = getattr(FIAT, fiat_name)(cell, *args, **{i: j for i, j in params.items() if i != "order"})

    value_size = 1
    for i in e.value_shape():
        value_size *= i
    edofs = [list(i.values()) for i in e.entity_dofs().values()]
    return edofs, lambda points: list(e.tabulate(0, points).values())[0].T.reshape(
        points.shape[0], value_size, -1)


formats = {
    "symfem": symfem_format,
    "basix": basix_format,
    "basix.ufl": basix_ufl_format,
    "bempp": string_format,
    "ufl": string_format,
    "fiat": fiat_format,
}

examples = {
    "symfem": symfem_example,
    "basix": basix_example,
    "basix.ufl": basix_ufl_example,
    "bempp": bempp_example,
    "ufl": ufl_legacy_example,
    "fiat": fiat_example,
}

verifications = {
    "symfem": symfem_verify,
    "basix": basix_verify,
    "basix.ufl": basix_ufl_verify,
    "fiat": fiat_verify,
}
