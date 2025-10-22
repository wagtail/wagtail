"""
Custom Django serializers for Wagtail natural key serialization.

This part provides enhanced serializers that handle Wagtail-specific
natural keys and StreamField chooser blocks to ensure proper serialization/deserialization.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from typing import Any, Dict

from django.apps import apps
from django.core.serializers import register_serializer
from django.core.serializers.base import DeserializationError
from django.core.serializers.json import Deserializer as JSONDeserializer
from django.core.serializers.json import Serializer as JSONSerializer

from wagtail.blocks import ChooserBlock, StreamValue
from wagtail.documents import get_document_model
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.fields import StreamField
from wagtail.images import get_image_model
from wagtail.images.blocks import ImageChooserBlock, ImageBlock
from wagtail.models import Collection, Page, Site
from wagtail.snippets.blocks import SnippetChooserBlock

Image = get_image_model()
Document = get_document_model()


def file_checksum(django_file) -> str | None:
    #Calculate SHA1 checksum of a Django file.
    if not django_file:
        return None
    try:
        pos = django_file.tell()
    except Exception:
        pos = None
    try:
        if hasattr(django_file, "seek"):
            django_file.seek(0)
       
        h = hashlib.sha1()
        for chunk in iter(lambda: django_file.read(1024 * 1024), b""):
            h.update(chunk)
        return h.hexdigest()
    finally:
        try:
            if pos is not None and hasattr(django_file, "seek"):
                django_file.seek(pos)
        except Exception:
            pass


def collection_path_tuple(collection: Collection) -> tuple[str, ...]:
   #root to leaf
    names = []
    node = collection
    while node is not None:
        names.append(node.name)
        node = node.get_parent() if node.depth > 1 else None
    return tuple(reversed(names))


def site_natural_dict(site: Site) -> Dict[str, Any]:
    
    return {"_type": "wagtail.site", "hostname": site.hostname, "port": site.port}


def page_natural_dict(page: Page) -> Dict[str, Any]:
    
    locale_code = getattr(getattr(page, "locale", None), "language_code", None)
    return {"_type": "wagtail.page", "url_path": page.url_path, "locale": locale_code}


def collection_natural_dict(collection: Collection) -> Dict[str, Any]:
   
    return {"_type": "wagtail.collection", "path": collection_path_tuple(collection)}


def image_natural_dict(img: Image) -> Dict[str, Any]:
    
    return {
        "_type": "wagtail.image",
        "checksum": file_checksum(getattr(img, "file", None)),
        "filename": img.file.name.rsplit("/", 1)[-1] if getattr(img, "file", None) else None,
        "collection": collection_natural_dict(img.collection) if img.collection_id else None,
    }


def document_natural_dict(doc: Document) -> Dict[str, Any]:
    
    return {
        "_type": "wagtail.document",
        "checksum": file_checksum(getattr(doc, "file", None)),
        "filename": doc.file.name.rsplit("/", 1)[-1] if getattr(doc, "file", None) else None,
        "collection": collection_natural_dict(doc.collection) if doc.collection_id else None,
    }


def resolve_collection_by_path(path: Iterable[str]) -> Collection:
    
    names = list(path)
    if not names:
        raise DeserializationError("Empty collection path")
    node = Collection.objects.get(depth=1, name=names[0])
    for name in names[1:]:
        node = Collection.objects.get(parent=node, name=name)
    return node


def resolve_natural(d: Dict[str, Any]) -> Any:
    
    t = d.get("_type")
    if t == "wagtail.site":
        return Site.objects.get(hostname=d["hostname"], port=d["port"])
    if t == "wagtail.collection":
        return resolve_collection_by_path(d["path"])
    if t == "wagtail.page":
        qs = Page.objects
        if d.get("locale"):
            qs = qs.filter(locale__language_code=d["locale"])
        return qs.get(url_path=d["url_path"])
    if t == "wagtail.image":
        qs = Image.objects
        if coll := d.get("collection"):
            qs = qs.filter(collection=resolve_natural(coll))
        if d.get("checksum"):
            
            pass
        if d.get("filename"):
            return qs.get(file__icontains=d["filename"])
        raise DeserializationError("Cannot resolve wagtail.image without filename/checksum")
    if t == "wagtail.document":
        qs = Document.objects
        if coll := d.get("collection"):
            qs = qs.filter(collection=resolve_natural(coll))
        if d.get("checksum"):
            pass
        if d.get("filename"):
            return qs.get(file__icontains=d["filename"])
        raise DeserializationError("Cannot resolve wagtail.document without filename or checksum")
    if t and t.startswith("model:"):
        label = t.split(":", 1)[1]
        model = apps.get_model(label)
        natural = d["natural"]
        if hasattr(model._default_manager, "get_by_natural_key"):
            if isinstance(natural, (list, tuple)):
                return model._default_manager.get_by_natural_key(*natural)
            return model._default_manager.get_by_natural_key(**natural)  
        if isinstance(natural, dict) and "pk" in natural:
            return model._default_manager.get(pk=natural["pk"])
        raise DeserializationError(f"No way to resolve model with label {label}")
    raise DeserializationError(f"Unknown natural ref: {d}")


def transform_stream_for_dump(value: Any) -> Any:
    
    if isinstance(value, StreamValue):
        stream_block = value.stream_block

        def recurse(data: Any, block: Any | None = None) -> Any:
            
            if isinstance(block, ChooserBlock):
                obj = data
                
                if not hasattr(obj, "_meta") and hasattr(block, "target_model") and data is not None:
                    obj = block.target_model.objects.get(pk=data)
                if isinstance(block, (ImageChooserBlock, ImageBlock)):
                    return image_natural_dict(obj) if obj else None
                if isinstance(block, DocumentChooserBlock):
                    return document_natural_dict(obj) if obj else None
               
                from wagtail.blocks import PageChooserBlock as _PageChooserBlock  

                if isinstance(block, _PageChooserBlock):
                    return page_natural_dict(obj) if obj else None
                if isinstance(block, SnippetChooserBlock):
                    return {
                        "_type": f"model:{obj._meta.label_lower}",
                        "natural": getattr(obj, "natural_key", lambda: {"pk": obj.pk})(),
                    }
                return data

            
            if hasattr(block, "child_blocks") and isinstance(data, dict):
                out = {}
                for name, child in block.child_blocks.items():
                    out[name] = recurse(data.get(name), child)
                return out
            if hasattr(block, "child_block") and isinstance(data, list):
                return [recurse(item, block.child_block) for item in data]
            if hasattr(block, "stream_block") and isinstance(data, list):
              
                return [recurse(item.get("value"), block.stream_block) for item in data]
            return data

        
        raw = stream_block.get_prep_value(value)  
        out_list = []
        for child in raw:
            block = stream_block.child_blocks[child["type"]]
            out_list.append(
                {
                    "type": child["type"],
                    "value": recurse(child.get("value"), block),
                }
            )
        return out_list
    
    return value


def _resolve_stream_for_load(data: Any) -> Any:
    
    if isinstance(data, dict) and "_type" in data:
        obj = resolve_natural(data)
        return getattr(obj, "pk", obj)
    if isinstance(data, list):
        return [_resolve_stream_for_load(x) for x in data]
    if isinstance(data, dict):
        return {k: _resolve_stream_for_load(v) for k, v in data.items()}
    return data


class WagtailNaturalSerializer(JSONSerializer):
    
    internal_use_only = False

    def handle_field(self, obj, field):
        if isinstance(field, StreamField):
            self._current[field.name] = transform_stream_for_dump(field.value_from_object(obj))
            return
        super().handle_field(obj, field)

    def handle_fk_field(self, obj, field):
        rel = getattr(obj, field.name)
        if rel is None:
            self._current[field.name] = None
            return
        if isinstance(rel, Site):
            self._current[field.name] = site_natural_dict(rel)
            return
        if isinstance(rel, Page):
            self._current[field.name] = page_natural_dict(rel)
            return
        if isinstance(rel, Collection):
            self._current[field.name] = collection_natural_dict(rel)
            return
        if isinstance(rel, Image):
            self._current[field.name] = image_natural_dict(rel)
            return
        if isinstance(rel, Document):
            self._current[field.name] = document_natural_dict(rel)
            return
        
        self._current[field.name] = {
            "_type": f"model:{rel._meta.label_lower}",
            "natural": getattr(rel, "natural_key", lambda: {"pk": rel.pk})(),
        }


def WagtailNaturalDeserializer(stream_or_string, **options):
    
    for obj in JSONDeserializer(stream_or_string, **options):
        model = obj.object.__class__
        
        for f in model._meta.fields:
            if isinstance(f, StreamField):
                continue
            try:
                val = getattr(obj.object, f.name)
            except Exception:
                val = None
            if isinstance(val, dict) and "_type" in val:
                setattr(obj.object, f.name, resolve_natural(val))
        
        for f in model._meta.fields:
            if isinstance(f, StreamField):
                raw = getattr(obj.object, f.name, None)
                if raw:
                    setattr(obj.object, f.name, _resolve_stream_for_load(raw))
        yield obj



register_serializer("wagtail_natural", WagtailNaturalSerializer)
