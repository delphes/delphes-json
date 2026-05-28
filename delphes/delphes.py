import json
import ROOT

from argparse import ArgumentParser
from pathlib import Path

from .tcl2py import tcl2py


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--card", help="detector card file name", required=True)
    parser.add_argument("--format", help="input file format (HepMC2, HepMC3, LHEF, STDHEP, Pythia8)", required=True)
    parser.add_argument("--input", help="input file name", required=True)
    parser.add_argument("--output", help="output file name", required=True)
    args = parser.parse_args()
    return Path(args.card), args.format.lower(), Path(args.input), Path(args.output)


def read_card(card_file):
    suffix = card_file.suffix
    namespace = {}

    if suffix == ".tcl":
        content = tcl2py(card_file)
        exec(content, namespace)
        return json.dumps(namespace["card"])

    if suffix == ".py":
        content = card_file.read_text(encoding="utf-8")
        exec(content, namespace)
        return json.dumps(namespace["card"])

    if suffix == ".json":
        return card_file.read_text(encoding="utf-8")

    raise ValueError(f"unrecognized detector card file format: {suffix}")


def delphes():
    card, format, input, output = parse_args()

    ROOT.gSystem.Load("libDelphes")

    input_formats = {
        "hepmc2": ROOT.DelphesHepMC2Reader,
        "hepmc3": ROOT.DelphesHepMC3Reader,
        "lhef": ROOT.DelphesLHEFReader,
        "stdhep": ROOT.DelphesSTDHEPReader,
    }
    try:
        input_formats["pythia8"] = ROOT.DelphesPythia8Reader
    except AttributeError:
        pass

    if not card.is_file():
        raise FileNotFoundError(f"detector card file not found: {card}")

    if format not in input_formats:
        raise ValueError(f"unrecognized input file format: {format}")

    if not input.is_file():
        raise FileNotFoundError(f"input file not found: {input}")

    if output.exists():
        raise FileExistsError(f"output file already exists: {output}")

    conf_data = read_card(card)

    conf_reader = ROOT.ExRootConfReader()
    conf_reader.ReadData(conf_data)

    reader = input_formats[format]()
    reader.OpenInputFile(str(input))

    output_file = ROOT.TFile(str(output), "CREATE")

    writer = ROOT.ExRootTreeWriter(output_file, "Delphes")

    if format in {"lhef", "stdhep"}:
        event_class = ROOT.LHEFEvent.Class()
        weight_class = ROOT.LHEFWeight.Class()
    else:
        event_class = ROOT.HepMCEvent.Class()
        weight_class = ROOT.Weight.Class()

    branch_event = writer.NewBranch("Event", event_class)
    branch_weight = writer.NewBranch("Weight", weight_class)

    module = ROOT.Delphes("Delphes")
    module.SetConfReader(conf_reader)
    module.SetTreeWriter(writer)

    arrays = [module.ExportArray(name) for name in ("allParticles", "stableParticles", "partons")]

    lhef_reader = None
    if format == "pythia8" and reader.ReadLHEF():
        lhef_reader = ROOT.DelphesLHEFReader()
        lhef_reader.OpenInputFile(reader.FileNameLHEF())

        lhef_branch_event = writer.NewBranch("EventLHEF", ROOT.LHEFEvent.Class())
        lhef_branch_weight = writer.NewBranch("WeightLHEF", ROOT.LHEFWeight.Class())

        lhef_arrays = [module.ExportArray(name) for name in ("allParticlesLHEF", "stableParticlesLHEF", "partonsLHEF")]

    factory = module.GetFactory()
    module.InitTask()
    progress = ROOT.ExRootProgressBar(-1)
    event_counter = 0

    while reader.ReadEvent(factory, *arrays):
        event_counter += 1

        if lhef_reader:
            lhef_reader.ReadEvent(factory, *lhef_arrays)

        if reader.EventReady():
            module.ProcessTask()

            reader.AnalyzeEvent(branch_event, event_counter)
            reader.AnalyzeWeight(branch_weight)

            if lhef_reader:
                lhef_reader.AnalyzeEvent(lhef_branch_event, event_counter)
                lhef_reader.AnalyzeWeight(lhef_branch_weight)

            writer.Fill()

        for obj in (writer, module, reader, lhef_reader):
            if obj:
                obj.Clear()

        progress.Update(0, event_counter)

    progress.Update(0, event_counter, ROOT.kTRUE)
    progress.Finish()

    reader.CloseInputFile()
    if lhef_reader:
        lhef_reader.CloseInputFile()

    module.FinishTask()
    writer.Write()


def main():
    try:
        delphes()
    except Exception as e:
        print(f"** ERROR: {e}")


if __name__ == "__main__":
    main()
