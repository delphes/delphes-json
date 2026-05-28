import numpy as np
import tkinter as tk

from argparse import ArgumentParser
from itertools import batched, groupby
from pathlib import Path

script = r"""
proc format_string {s} {
    if {[regexp {\n} $s]} {
        return "'''$s'''"
    } else {
        return "'$s'"
    }
}

proc dict2py value {
    set temp_vars [list EtaBins PhiBins eta i pi]
    regexp {^value is a (.*?) with a refcount} [::tcl::unsupported::representation $value] -> type
    switch $type {
        string {
            return [format_string $value]
        }
        dict {
            set tmp {}
            foreach {k v} [dict map {k v} $value {dict2py $v}] {
                if {$k ni $temp_vars} {
                    lappend tmp [format_string $k]:$v
                }
            }
            return \{[join $tmp ,]\}
        }
        list {
            set tmp [lmap v $value {dict2py $v}]
            return \[[join $tmp ,]\]
        }
        int - double {
            return [expr {$value}]
        }
        booleanString {
            return [expr {$value ? True : False}]
        }
        default {
            if {$value eq "null"} {
                return $value
            } elseif {[string is integer -strict $value]} {
                return [expr {$value}]
            } elseif {[string is double -strict $value]} {
                return [expr {$value}]
            } elseif {[string is boolean -strict $value]} {
                return [expr {$value ? True : False}]
            }
            return [format_string $value]
        }
    }
}

proc module {class module body} {
    namespace eval $module [list set Class $class]
    uplevel 1 [list namespace eval $module $body]
}

interp alias {} add {} lappend

proc tcl2py card {
    eval $card

    set cardDict [dict create ExecutionPath $ExecutionPath]

    foreach module $ExecutionPath {
        set vars [info vars ${module}::*]

        set names [lmap v $vars {regsub ^::${module}:: $v {}}]

        set moduleDict {}

        foreach v $vars n $names {
            dict set moduleDict $n [set $v]
        }

        dict set cardDict $module $moduleDict
    }
    return "card = [dict2py $cardDict]"
}
"""


def optimize_eta_bins(bins):
    n = len(bins)
    if n < 3:
        return bins, []
    non_linear = np.abs(np.diff(np.diff(bins))) > 1e-14
    imax, imin = non_linear.argmax(), non_linear.argmin()
    if imax == 0 and non_linear[0]:
        if imin == 0:
            return bins, []
        else:
            return bins[:imin], bins[imin:]
    imax = n if imax == 0 else imax + 2
    start, step = bins[0], bins[1] - bins[0]
    return f"[{start:g} + i * {step:g} for i in range({imax})]", bins[imax:]


def optimize_eta_phi_bins(card):
    for module in card.values():
        if not isinstance(module, dict) or "EtaPhiBins" not in module:
            continue
        new_bins = []
        for phi, group in groupby(batched(module["EtaPhiBins"], 2), key=lambda p: p[1]):
            phi = len(phi) - 1 if isinstance(phi, list) else phi
            eta_bins = [item for eta, _ in group for item in (eta if isinstance(eta, list) else [eta])]
            while eta_bins:
                new_eta_bins, eta_bins = optimize_eta_bins(eta_bins)
                new_bins.extend([new_eta_bins, phi])
        module["EtaPhiBins"] = new_bins


def format(value, level=1):
    sep = "\n" + " " * 4 * level
    end = "\n" + " " * 4 * (level - 1)
    if isinstance(value, dict):
        items = [f"{k}={format(v, level + 1)}" for k, v in value.items()]
        return "dict(" + sep + ("," + sep).join(items) + end + ")"
    if isinstance(value, list):
        items = [format(v, level + 1) for v in value]
        return "[" + sep + ("," + sep).join(items) + end + "]"
    if isinstance(value, str):
        if value.startswith("[") and "for i in range" in value:
            return value
        lines = [v.replace("\\", "").strip() for v in value.splitlines()]
        if len(lines) > 1:
            return "'''" + sep + sep.join(lines) + end + "'''"
        else:
            return repr(lines[0])
    if isinstance(value, float):
        return f"{value:g}"
    return repr(value)


def source(file):
    global card_dir, tcl
    path = card_dir / file
    content = path.read_text(encoding="utf-8")
    tcl.eval(content)


def tcl2py(card_file):
    global card_dir, tcl

    card_dir = card_file.parent

    content = card_file.read_text(encoding="utf-8")

    tcl = tk.Tcl()

    tcl.createcommand("source", source)
    tcl.eval(script)

    result = tcl.call("tcl2py", content)

    namespace = {}
    exec(result, namespace)
    card = namespace["card"]

    optimize_eta_phi_bins(card)

    return "card = " + format(card)


def main():
    parser = ArgumentParser()
    parser.add_argument("card", help="detector card file name")

    args = parser.parse_args()

    card_file = Path(args.card)
    output = tcl2py(card_file)

    try:
        from black import format_str, FileMode
    except ModuleNotFoundError:
        print(output)
    else:
        print(format_str(output, mode=FileMode()))


if __name__ == "__main__":
    main()
