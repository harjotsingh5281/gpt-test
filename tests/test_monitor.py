import unittest
from datetime import date
from monitor import parse, CheckError
TODAY = date(2026, 11, 20)
HEAD = "Choose Date\nTest\nTCF Canada - Computer\nToronto\n"
def pill(day, month="Dec", count=1):
    return f"{month} {day}\nFRI\n{count} Slots"
def card(day, month="Dec", year=2026, count=1, select=True, deadline="MON 07 Dec 2026"):
    return (f"TCF Canada\nGroup Test Time\n{count}\nGroup Test Time\nFRI {day} {month} {year}\n"
            "02:00 PM - 05:00 PM\nExpected Result Date: Fri 22 Jan 2027\nToronto\nComputer\n"
            "Oral Time:\n09:20 AM - 09:40 AM\nCAD $452\n" +
            ("Select\n" if select else "") + f"Registration Deadline: {deadline}\n")
class Tests(unittest.TestCase):
    def test_no_december_in_observed_calendar(self):
        body = HEAD + card(27, "Nov", deadline="MON 23 Nov 2026") + card(15, "Jan", 2027, 26, deadline="MON 11 Jan 2027")
        found, n = parse(body, [pill(27, "Nov"), pill(15, "Jan", 26)], TODAY)
        self.assertEqual((found, n), ({}, 2))
    def test_inclusive_target_dates(self):
        found, _ = parse(HEAD + card(9) + card(10) + card(31) + card(1, "Jan", 2027), [pill(9), pill(10), pill(31), pill(1, "Jan")], TODAY)
        self.assertEqual({s["date"] for s in found.values()}, {"2026-12-10", "2026-12-31"})
    def test_result_date_is_not_exam_date(self):
        found, _ = parse(HEAD + card(27, "Nov", deadline="MON 23 Nov 2026").replace("Fri 22 Jan 2027", "Thu 10 Dec 2026"), [pill(27, "Nov")], TODAY)
        self.assertEqual(found, {})
    def test_zero_or_missing_select(self):
        for item, button in [(card(20, count=0), pill(20, count=0)), (card(20, select=False), pill(20))]:
            found, _ = parse(HEAD + item, [button], TODAY)
            self.assertEqual(found, {})
    def test_missing_date_button_fails_closed(self):
        with self.assertRaises(CheckError): parse(HEAD + card(20), [], TODAY)
    def test_wrong_exam_empty_calendar_expired_deadline(self):
        with self.assertRaises(CheckError): parse("TEF Canada\n" + card(10), [pill(10)], TODAY)
        with self.assertRaises(CheckError): parse(HEAD + "No sessions", [], TODAY)
        found, _ = parse(HEAD + card(10, deadline="THU 19 Nov 2026"), [pill(10)], TODAY)
        self.assertEqual(found, {})
if __name__ == "__main__": unittest.main()
