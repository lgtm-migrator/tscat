#!/usr/bin/env python

import unittest
from ddt import ddt, data, unpack

import tscat.orm_sqlalchemy
from tscat import Event, Catalogue, get_events, save, discard, get_catalogues

import datetime as dt


@ddt
class TestCatalogue(unittest.TestCase):
    def setUp(self) -> None:
        tscat._backend = tscat.orm_sqlalchemy.Backend(testing=True)  # create a memory-database for tests

        self.events = [
            Event(dt.datetime.now(), dt.datetime.now() + dt.timedelta(days=1), "Patrick"),
            Event(dt.datetime.now(), dt.datetime.now() + dt.timedelta(days=2), "Patrick"),
            Event(dt.datetime.now(), dt.datetime.now() + dt.timedelta(days=3), "Patrick"),
        ]

        save()

    @data(
        ("Catalogue Name", "", {}),
        ("Catalogue Name", "Patrick", {}),
        ("Catalogue Name", "Patrick", {'field': 2}),
        ("Catalogue Name", "Patrick", {'field_': 2}),
        ("Catalogue Name", "Patrick", {'field_with_underscores': 2}),
        ("Catalogue Name", "Patrick", {'field': 2.0}),
        ("Catalogue Name", "Patrick", {'field': "2"}),
        ("Catalogue Name", "Patrick", {'field': True}),
        ("Catalogue Name", "Patrick", {'field': dt.datetime.now()}),
        ("Catalogue Name", "Patrick", {'field': 2}),
        ("Catalogue Name", "Patrick", {'field': 2, 'Field': 3}),
        ("Catalogue Name", "Patrick",
         {'field': 2, 'field2': 3.14, 'field3': "str", 'field4': True, 'field5': dt.datetime.now()}),
    )
    @unpack
    def test_constructor_various_combinations_all_ok(self, name, author, attrs):
        e = Catalogue(name, author, **attrs)

        self.assertEqual(e.name, name)
        self.assertEqual(e.author, author)

        for k, v in attrs.items():
            self.assertEqual(e.__getattribute__(k), v)

        attr_repr = ', '.join(f'{k}={v}' for k, v in attrs.items())
        self.assertRegex(f'{e}',
                         r'^Catalogue\(name=' + name + r', author=' + author +
                         r', predicate=None\) attributes\(' + attr_repr + r'\)$')

    @data(
        ("", "", {}),
        ("", "", {}),
        ("Catalogue Name", "", {"_invalid": 2}),
        ("Catalogue Name", "", {"'invalid'": 2}),
        ("Catalogue Name", "", {"invalid'": 2}),
        ("Catalogue Name", "", {'"invalid"': 2}),
        ("Catalogue Name", "", {"\nvalid": 2}),
        ("Catalogue Name", "", {"nvalid\\\'": 2}),
    )
    @unpack
    def test_constructor_various_combinations_value_errorl(self, name, author, attrs):
        with self.assertRaises(ValueError):
            assert Catalogue(name, author, **attrs)

    def test_unequal_catalogues(self):
        a, b = Catalogue("Catalogue Name1", "Patrick"), Catalogue("Catalogue Name2", "Patrick")
        self.assertNotEqual(a, b)

        a, b = Catalogue("Catalogue Name", "Patrick", attr1=20), Catalogue("Catalogue Name", "Patrick", attr1=10)
        self.assertNotEqual(a, b)

        a, b = Catalogue("Catalogue Name", "Patrick", attr1=20), Catalogue("Catalogue Name", "Patrick", attr2=20)
        self.assertNotEqual(a, b)

    def test_constructor_with_dynamic_attribute_manual_access(self):
        dt_val = dt.datetime.now()
        c = Catalogue("Catalogue Name", "Patrick",
                      field_int=100, field_float=1.234, field_str="string-test", field_bool=True, field_dt=dt_val)

        self.assertEqual(c.name, "Catalogue Name")
        self.assertEqual(c.author, "Patrick")

        self.assertEqual(c.field_int, 100)
        self.assertEqual(c.field_float, 1.234)
        self.assertEqual(c.field_str, "string-test")
        self.assertEqual(c.field_bool, True)
        self.assertEqual(c.field_dt, dt_val)

    def test_add_and_get_empty_catalogues(self):
        catalogues = [Catalogue("Catalogue Name1", "Patrick"), Catalogue("Catalogue Name2", "Patrick")]
        cat_list = get_catalogues()
        self.assertListEqual(catalogues, cat_list)

    def test_add_and_get_empty_catalogues_discard_and_save(self):
        Catalogue("Catalogue Name1", "Patrick")
        Catalogue("Catalogue Name2", "Patrick")

        discard()

        cat_list = get_catalogues()
        self.assertListEqual([], cat_list)

        c = Catalogue("Catalogue Name2", "Patrick")

        cat_list = get_catalogues()
        self.assertListEqual([c], cat_list)

        save()

        cat_list = get_catalogues()
        self.assertListEqual([c], cat_list)

        c2 = Catalogue("Catalogue Name2", "Patrick")

        cat_list = get_catalogues()
        self.assertListEqual([c, c2], cat_list)

        discard()

        cat_list = get_catalogues()
        self.assertListEqual([c], cat_list)

    def test_add_events_to_catalogue_constructor(self):
        c = Catalogue("Catalogue Name", "Patrick", events=self.events)

        event_list = get_events(c)
        self.assertListEqual(event_list, self.events)

        c.remove_events(self.events[0])

        event_list = get_events(c)
        self.assertListEqual(event_list, self.events[1:])

    def test_add_events_to_catalogue_via_method(self):
        c = Catalogue("Catalogue Name", "Patrick")
        c.add_events(self.events)

        event_list = get_events(c)
        self.assertListEqual(self.events, event_list)

        c.remove_events(self.events[0])
        event_list = get_events(c)
        self.assertListEqual(event_list, self.events[1:])

    def test_add_event_multiple_times_to_catalogue(self):
        c = Catalogue("Catalogue Name", "Patrick")
        c.add_events(self.events[0])
        with self.assertRaises(ValueError):
            c.add_events(self.events[0])

    def test_catalogues_of_event(self):
        a = Catalogue("Catalogue Name A", "Patrick")
        a.add_events(self.events[0])
        a.add_events(self.events[1])
        b = Catalogue("Catalogue Name B", "Patrick")
        b.add_events(self.events[0])

        cat_list = get_catalogues(self.events[0])
        self.assertListEqual(cat_list, [a, b])

        cat_list = get_catalogues(self.events[1])
        self.assertListEqual(cat_list, [a])
