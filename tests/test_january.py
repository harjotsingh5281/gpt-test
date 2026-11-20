import unittest
from datetime import date
from monitor_january import parse, CheckError, START, END, STATE_TITLE
TODAY = date(2026, 11, 20)
HEAD = "Choose Date\nTest\nTCF Canada - Computer\nToronto\n"
def pill(day, month="Jan", count=5):
    return f"{month} {day}\nFRI\n{count} Slots"
def card(day, month="Jan", year=2027, count=5, select=True):
    return (f"TCF Canada\n{count}\nGroup Test Time\nFRI {day} {month} {year}\n"
            "02:00 PM - 05:00 PM\nExpected Result Date: Fri 12 Feb 2027\n"
            "Oral Time: 09:20 AM - 09:40 AM\nToronto\nComputer\nCAD $452\n" +
            ("Select\n" if select else "") + "Registration Deadline: MON 28 Dec 2026\n")
class JanuaryTests(unittest.TestCase):
    def test_boundaries_and_year(self):
        self.assertEqual((str(START), str(END)), ("2027-01-01", "2027-01-31"))
        self.assertIn("January", STATE_TITLE)
    def test_finds_only_january_2027(self):
        body = HEAD + card(31, "Dec", 2026) + card(1) + card(15) + card(31) + card(1, "Feb", 2027)
        buttons = [pill(31,"Dec"), pill(1), pill(15), pill(31), pill(1,"Feb")]
        slots, count = parse(body, buttons, TODAY)
        self.assertEqual(count, 5)
        self.assertEqual({s["date"] for s in slots.values()},
                         {"2027-01-01","2027-01-15","2027-01-31"})
    def test_no_matching_january(self):
        slots, _ = parse(HEAD + card(20,"Dec",2026) + card(2,"Feb",2027),
                         [pill(20,"Dec"),pill(2,"Feb")], TODAY)
        self.assertFalse(slots)
    def test_missing_select_and_no_seats(self):
        for c,b in [(card(15, count=0),pill(15,count=0)),(card(15,select=False),pill(15))]:
            slots,_=parse(HEAD+c,[b],TODAY)
            self.assertFalse(slots)
    def test_does_not_confuse_result_dates(self):
        body=HEAD+card(20,"Dec",2026).replace("Fri 12 Feb 2027","Fri 15 Jan 2027")
        slots,_=parse(body,[pill(20,"Dec")],TODAY)
        self.assertFalse(slots)
    def test_mismatched_slots_fails_closed(self):
        with self.assertRaises(CheckError):
            parse(HEAD+card(15),[],TODAY)
if __name__ == "__main__":
    unittest.main()
# AUTOMATED_FALLBACK_HEARTBEAT: 2026-11-20 first verified trigger
