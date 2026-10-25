"""
بيكتب عينات مجموعة التطوير (dev set) كملفات JSON بنفس صيغة run_baseline:

    code_vs_doc : {"id", "language", "code", "doc": {"content", "explanation_type"}}
                  {"id", "language", "code", "doc_source": "python_docstrings"}
    code_vs_code: {"id", "language", "code_a", "code_b"}

    python -m evaluation.dev_set.build_samples

الوسم (الجواب الصح) مش هون — هو بـ labels_code_vs_doc.csv و labels_code_vs_code.csv،
لحتى يضل الوسم منفصل عن العينة متل ما بيطلب دليل الوسم.
العينات real_book_* مأخوذة من tests/fixtures/real_docs_book.json (توثيقات حقيقية من Mongo).
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE.parent.parent / "core_ai" / "tests" / "fixtures" / "real_docs_book.json"


def low(content: str) -> dict:
    return {"content": content.strip() + "\n", "explanation_type": "low_level"}


def high(content: str) -> dict:
    return {"content": content.strip() + "\n", "explanation_type": "high_level"}


# ═════════════════════════════════════════════════════════════════════
# Code vs Doc
# ═════════════════════════════════════════════════════════════════════

CODE_VS_DOC = [
    {
        "id": "doc_user_repo",
        "language": "python",
        "code": '''
class UserRepository:
    def __init__(self, store: dict):
        self.store = store

    def get(self, uid: int) -> Optional[dict]:
        return self.store.get(uid)

    def add(self, user: dict) -> None:
        self.store[user["id"]] = user

    def remove(self, uid: int) -> None:
        if uid not in self.store:
            raise ValueError("unknown user")
        del self.store[uid]

    def count(self) -> int:
        return len(self.store)
''',
        "doc": low('''
## Class: UserRepository
**Purpose:** In-memory storage of user records.

### Constructor: __init__
**Description:** Stores the backing dictionary.

### Method: get
**Description:** Returns the user with the given id.
**Returns:** dict - the user record.
**Error Handling:** Raises KeyError if the user does not exist.

### Method: add
**Description:** Adds a user after validating the email format.

### Method: remove
**Description:** Removes the user with the given id from the store.

### Method: count
**Description:** Returns the number of stored users.
**Returns:** int
'''),
    },
    {
        "id": "doc_http_client",
        "language": "python",
        "code": '''
class HttpClient:
    def __init__(self, base_url: str, timeout: float = 5):
        self.base_url = base_url
        self.timeout = timeout

    def fetch(self, path: str) -> str:
        return self._session.get(self.base_url + path, timeout=self.timeout).text

    def fetch_with_retry(self, path: str) -> str:
        for _ in range(3):
            try:
                return self.fetch(path)
            except IOError:
                continue
        raise IOError("failed after 3 attempts")

    def get_json(self, path: str) -> dict:
        return json.loads(self.fetch(path))

    def close(self):
        self._session.close()
''',
        "doc": low('''
## Class: HttpClient
**Purpose:** Small HTTP client bound to a base URL.

### Constructor: __init__
**Parameters:**
- **base_url**: root URL prepended to every path
- **timeout**: request timeout in seconds (default 5)

### Method: fetch
**Description:** Downloads the resource at path. Results are cached, so repeated calls for the same path do not hit the network.
**Returns:** str - response body

### Method: fetch_with_retry
**Description:** Fetches the path, retrying up to 3 times on IO errors before raising IOError.

### Method: get_json
**Description:** Fetches the path and parses the body as JSON.
**Returns:** dict
'''),
    },
    {
        "id": "doc_rectangle_high",
        "language": "python",
        "code": '''
class Rectangle:
    def __init__(self, w: float, h: float):
        self.w = w
        self.h = h

    def area(self) -> float:
        return self.w * self.h

    def perimeter(self) -> float:
        return self.w * self.h

    def scale(self, k: float) -> None:
        self.w *= k
        self.h *= k
''',
        "doc": high('''
---
## Executive Summary
Rectangle models a rectangle and computes its basic geometry.

## Class: Rectangle
Purpose:
Represents a rectangle defined by its width and height.

### Constructor: __init__(self, w, h)
Logic Flow:
1. Stores the width and height.

### Method: area(self)
Logic Flow:
1. Multiplies width by height and returns the result.

### Method: perimeter(self)
Logic Flow:
1. Returns twice the sum of width and height.

### Method: scale(self, k)
Logic Flow:
1. Creates and returns a new Rectangle whose sides are multiplied by k.
2. The original rectangle is left unchanged.
'''),
    },
    {
        "id": "doc_text_utils_docstrings",
        "language": "python",
        "doc_source": "python_docstrings",
        "code": '''
class TextUtils:
    def parse_date(self, s: str):
        """Parse an ISO date string (YYYY-MM-DD). Returns None if the string is invalid."""
        return datetime.strptime(s, "%Y-%m-%d")

    def normalize(self, s: str) -> str:
        """Lowercase the text and strip surrounding whitespace."""
        return s.lower()

    def save(self, path: str, text: str) -> None:
        """Save the text to path."""
        if os.path.exists(path):
            os.remove(path)
        with open(path, "w") as f:
            f.write(text)

    def word_count(self, s: str) -> int:
        """Return the number of whitespace-separated words in s."""
        return len(s.split())
''',
    },
    {
        "id": "doc_mailer_params",
        "language": "python",
        "code": '''
class Mailer:
    def send(self, to: str, subject: str, body: str, retries: int = 5) -> bool:
        for _ in range(retries):
            if self._smtp.send(to, subject, body):
                return True
        return False

    def format_name(self, first: str, last: str) -> str:
        return f"{last}, {first}"
''',
        "doc": low('''
## Class: Mailer
**Purpose:** Sends e-mail through an SMTP connection.

### Method: send
**Description:** Sends a message, retrying on failure.
**Parameters:**
- **to**: recipient address
- **subject**: message subject
- **body**: message body
- **retries**: number of attempts (default 3)
**Returns:** bool - True if the message was sent.

### Method: format_name
**Description:** Formats a person's name as "Last, First".
**Returns:** str
'''),
    },
    {
        "id": "doc_counter_threadsafe",
        "language": "python",
        "code": '''
class Counter:
    def __init__(self):
        self.value = 0

    def increment(self) -> int:
        self.value += 1
        return self.value

    def reset(self) -> None:
        self.value = 0
''',
        "doc": low('''
## Class: Counter
**Purpose:** A thread-safe counter that can be shared between worker threads.

### Constructor: __init__
**Description:** Starts the counter at zero.

### Method: increment
**Description:** Atomically increments the counter under a lock and returns the new value.
**Returns:** int

### Method: reset
**Description:** Resets the counter to zero.
'''),
    },
    {
        "id": "doc_inventory_java",
        "language": "java",
        "code": '''
public class Inventory {
    private Map<String, Integer> stock = new HashMap<>();

    public Inventory() { }

    public int quantity(String sku) { return stock.getOrDefault(sku, 0); }

    public void remove(String sku, int n) {
        int q = quantity(sku);
        stock.put(sku, q - n);
    }

    public boolean has(String sku) { return stock.containsKey(sku); }
}
''',
        "doc": low('''
## Class: Inventory
**Purpose:** Tracks stock levels per SKU.

### Constructor: Inventory
**Description:** Creates an empty inventory.

### Method: quantity
**Description:** Returns the stock level for the given sku.
**Error Handling:** Throws IllegalArgumentException when the sku is unknown.

### Method: remove
**Description:** Removes n units of the sku. Throws IllegalStateException if there is not enough stock.

### Method: has
**Description:** Returns true if the sku exists in the inventory.
**Returns:** boolean
'''),
    },
]


def real_book_samples():
    names = {"6a721f2f4dba90f43665dc3c": "doc_real_book_high_1",
             "6aceb9997cc4fde32443cd3c": "doc_real_book_high_2",
             "6aceba627cc4fde32443cd4b": "doc_real_book_low"}
    for d in json.loads(FIXTURE.read_text(encoding="utf-8")):
        yield {"id": names[d["id"]], "language": "java", "code": d["code"],
               "doc": {"content": d["content"], "explanation_type": d["explanation_type"]},
               "source": f"ai_explanations/{d['id']}"}


# ═════════════════════════════════════════════════════════════════════
# Code vs Code
# ═════════════════════════════════════════════════════════════════════

def cc(id_, a, b, language="python"):
    return {"id": id_, "language": language, "code_a": a.strip() + "\n", "code_b": b.strip() + "\n"}


CODE_VS_CODE = [
    cc("cc_find_default", '''
class Store:
    def find(self, k: str) -> int:
        return self.d[k]
''', '''
class Store:
    def find(self, k: str) -> int:
        return self.d.get(k, -1)
'''),
    cc("cc_rename", '''
class Svc:
    def fetchUser(self, uid: int) -> dict:
        return self.db.load(uid)
''', '''
class Svc:
    def get_user(self, uid: int) -> dict:
        return self.db.load(uid)
'''),
    cc("cc_refactor_docstring", '''
class Cart:
    def total(self) -> float:
        s = 0
        for x in self.items:
            s += x.price
        return s
''', '''
class Cart:
    def total(self) -> float:
        """Sum of item prices."""
        return sum(x.price for x in self.items)
'''),
    cc("cc_default_change", '''
class Conn:
    def connect(self, host: str, timeout: int = 30) -> bool:
        return self.sock.open(host, timeout)
''', '''
class Conn:
    def connect(self, host: str, timeout: int = 5) -> bool:
        return self.sock.open(host, timeout)
'''),
    cc("cc_optional_param", '''
class Report:
    def render(self, data: list) -> str:
        return "\\n".join(map(str, data))
''', '''
class Report:
    def render(self, data: list, title: str = None) -> str:
        body = "\\n".join(map(str, data))
        if title:
            return title + "\\n" + body
        return body
'''),
    cc("cc_required_param", '''
class Api:
    def call(self, url: str) -> dict:
        return self.http.get(url)
''', '''
class Api:
    def call(self, url: str, token: str) -> dict:
        return self.http.get(url, headers={"Authorization": token})
'''),
    cc("cc_none_instead_of_raise", '''
class Repo:
    def get(self, uid: int) -> dict:
        if uid not in self.rows:
            raise KeyError(uid)
        return self.rows[uid]
''', '''
class Repo:
    def get(self, uid: int) -> dict:
        if uid not in self.rows:
            return None
        return self.rows[uid]
'''),
    cc("cc_comment_only", '''
class Calc:
    def add(self, a: int, b: int) -> int:
        # add two numbers
        return a + b
''', '''
class Calc:
    def add(self, a: int, b: int) -> int:
        # returns the sum
        return  a + b   # simple
'''),
    cc("cc_removed_method", '''
class Billing:
    def charge(self, amount: float) -> bool:
        return self.gw.charge(amount)

    def legacy_charge(self, amount: float) -> bool:
        return self.old_gw.charge(amount)
''', '''
class Billing:
    def charge(self, amount: float) -> bool:
        return self.gw.charge(amount)
'''),
    cc("cc_added_method", '''
class Shelf:
    def size(self) -> int:
        return len(self.items)
''', '''
class Shelf:
    def size(self) -> int:
        return len(self.items)

    def capacity(self) -> int:
        return self.max_items
'''),
    cc("cc_private_behavior", '''
class Parser:
    def parse(self, s: str) -> list:
        return self._clean(s).split(",")

    def _clean(self, s: str) -> str:
        return s.strip()
''', '''
class Parser:
    def parse(self, s: str) -> list:
        return self._clean(s).split(",")

    def _clean(self, s: str) -> str:
        return s.lower()
'''),
    cc("cc_method_to_property", '''
class Person:
    def full_name(self) -> str:
        return self.first + " " + self.last
''', '''
class Person:
    @property
    def full_name(self) -> str:
        return self.first + " " + self.last
'''),
    cc("cc_return_type", '''
class Order:
    def total(self) -> int:
        return sum(i.cents for i in self.items)
''', '''
class Order:
    def total(self) -> str:
        return f"{sum(i.cents for i in self.items) / 100:.2f}"
'''),
    cc("cc_extract_helper", '''
class Invoice:
    def total(self) -> float:
        return sum(l.qty * l.price for l in self.lines) * (1 + self.tax)
''', '''
class Invoice:
    def total(self) -> float:
        return self._subtotal() * (1 + self.tax)

    def _subtotal(self) -> float:
        return sum(l.qty * l.price for l in self.lines)
'''),
    cc("cc_class_removed", '''
class Payment:
    def pay(self, amount: float) -> bool:
        return True

class OldPayment:
    def pay(self, amount: float) -> bool:
        return False
''', '''
class Payment:
    def pay(self, amount: float) -> bool:
        return True
'''),
    cc("cc_java_account", '''
public class Account {
    private String id;
    private int balance;
    public Account(String id) { this.id = id; }
    public void withdraw(int amount) {
        if (amount > balance) { throw new IllegalStateException("insufficient funds"); }
        balance -= amount;
    }
    public int getBalance() { return balance; }
}
''', '''
public class Account {
    private String id;
    private int balance;
    private int limit;
    public Account(String id, int limit) { this.id = id; this.limit = limit; }
    public void withdraw(int amount) {
        balance -= amount;
    }
    public int getBalance() { return balance; }
}
''', language="java"),
    cc("cc_java_equivalent", '''
public class MathUtil {
    public int max(int a, int b) { return a > b ? a : b; }
}
''', '''
public class MathUtil {
    public int max(int a, int b) { return Math.max(a, b); }
}
''', language="java"),
]


def main() -> None:
    for mode, samples in (("code_vs_doc", CODE_VS_DOC + list(real_book_samples())),
                          ("code_vs_code", CODE_VS_CODE)):
        out = HERE / mode
        out.mkdir(exist_ok=True)
        for old in out.glob("*.json"):
            old.unlink()
        for s in samples:
            if "code" in s:
                s["code"] = s["code"].strip() + "\n"
            (out / f"{s['id']}.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{mode}: {len(samples)} samples → {out}")


if __name__ == "__main__":
    main()
