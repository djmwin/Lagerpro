import importlib
import os
import tempfile
import unittest


class LagerProTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ["LAGERPRO_DB"] = os.path.join(cls.tmp.name, "test.db")
        os.environ["LAGERPRO_SECRET"] = "test-secret"
        cls.module = importlib.import_module("web_app")
        cls.app = cls.module.app
        cls.app.config.update(TESTING=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        c = self.module.con()
        for table in (
            "email_log", "reorder_alerts", "movements", "serial_numbers",
            "load_carriers", "items", "containers", "articles", "users",
        ):
            c.execute(f"DELETE FROM {table}")
        c.execute("UPDATE warehouse_slots SET article_no=NULL,article_name=NULL,pallet_type=NULL,quantity=NULL,container_id=NULL,occupied_at=NULL,load_carrier_no=NULL,load_carrier_id=NULL,slot_status='frei',block_reason=NULL")
        c.commit()
        c.close()
        self.client = self.app.test_client()
        self.client.post("/setup", data={"full_name":"Admin", "username":"admin", "password":"sicheres-passwort"})
        self.client.post("/login", data={"username":"admin", "password":"sicheres-passwort"})

    def test_warehouse_layout_and_capacities(self):
        c = self.module.con()
        self.assertEqual(c.execute("SELECT COUNT(*) FROM warehouse_slots WHERE rack=1 AND level=1").fetchone()[0], 89)
        self.assertEqual(c.execute("SELECT COUNT(*) FROM warehouse_slots WHERE rack=8 AND level=1").fetchone()[0], 83)
        self.assertEqual(c.execute("SELECT capacity FROM warehouse_slots WHERE rack=1 AND level=1 AND position=21").fetchone()[0], 3)
        self.assertEqual(c.execute("SELECT capacity FROM warehouse_slots WHERE rack=1 AND level=1 AND position=24").fetchone()[0], 4)
        c.close()

    def test_article_master_and_manual_booking_create_complete_movement(self):
        response = self.client.post("/articles", data={
            "no":"A-100", "name":"Testartikel", "units_per_carton":"12",
            "cartons_per_pallet":"20", "ptype":"Euro", "rule":"Alle Ebenen",
        })
        self.assertEqual(response.status_code, 302)
        response = self.client.post("/manual-booking", data={
            "article_no":"A-100", "article_name":"Testartikel",
            "cartons_on_pallet":"20", "slot_code":"1/1/1",
        })
        self.assertEqual(response.status_code, 200)
        c = self.module.con()
        article = c.execute("SELECT * FROM articles WHERE article_no='A-100'").fetchone()
        movement = c.execute("SELECT * FROM movements ORDER BY id DESC LIMIT 1").fetchone()
        self.assertEqual(article["cpp"], 20)
        self.assertEqual(article["units_per_carton"], 12)
        self.assertEqual(movement["article_no"], "A-100")
        self.assertEqual(movement["quantity"], 20)
        c.close()

    def test_manual_booking_rejects_mixed_neighbor_pallet_types(self):
        self.client.post("/articles", data={"no":"EU", "name":"Euro", "units_per_carton":"1", "cartons_per_pallet":"1", "ptype":"Euro", "rule":"Alle Ebenen"})
        self.client.post("/articles", data={"no":"EW", "name":"Einweg", "units_per_carton":"1", "cartons_per_pallet":"1", "ptype":"Einweg", "rule":"Alle Ebenen"})
        self.client.post("/manual-booking", data={"article_no":"EU", "article_name":"Euro", "cartons_on_pallet":"1", "slot_code":"1/1/10"})
        response = self.client.post("/manual-booking", data={"article_no":"EW", "article_name":"Einweg", "cartons_on_pallet":"1", "slot_code":"1/1/11"})
        self.assertIn("dürfen nicht direkt nebeneinander", response.get_data(as_text=True))
        c = self.module.con()
        self.assertIsNone(c.execute("SELECT load_carrier_id FROM warehouse_slots WHERE rack=1 AND level=1 AND position=11").fetchone()[0])
        c.close()

    def test_reorder_alert_is_not_duplicated(self):
        c = self.module.con()
        c.execute("INSERT INTO articles(article_no,name,article_name,pallet_type,cpp,storage_rule,units_per_carton,min_stock,target_stock) VALUES('LOW','Niedrig','Niedrig','Euro',1,'Alle Ebenen',1,5,10)")
        c.commit(); c.close()
        original = self.module.send_system_email
        self.module.send_system_email = lambda *args, **kwargs: True
        try:
            self.module.check_reorders()
            self.module.check_reorders()
        finally:
            self.module.send_system_email = original
        c = self.module.con()
        self.assertEqual(c.execute("SELECT COUNT(*) FROM reorder_alerts WHERE article_no='LOW' AND status='offen'").fetchone()[0], 1)
        self.assertIsNotNone(c.execute("SELECT email_sent_at FROM reorder_alerts WHERE article_no='LOW'").fetchone()[0])
        c.close()


if __name__ == "__main__":
    unittest.main()
