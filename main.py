"""
this is an adaption layer for codecc
"""

import json
import xml.etree.ElementTree as ET
import sys
import os


WKFILE = os.path.realpath(__file__)
WKDIR = "/".join(WKFILE.split("/")[0:-1])


class InputInfo:
    def __init__(self):
        ##inputs
        self._rules = set()
        self._scan_path = ""
        self._skip_path = []
        self._increment_files = []
        self._result_dir = ""

    def parse_input(self):
        self._scan_path = os.environ.get("SOURCE_DIR", None)
        task_request_file = os.environ.get("TASK_REQUEST")
        self._result_dir = os.environ["RESULT_DIR"]
        with open(task_request_file, "r") as task_reader:
            task_request = json.load(task_reader)
        jsn = task_request["task_params"]
        incr_scan = jsn["incr_scan"]
        for rule in jsn["rules"]:
            self._rules.add(rule)
        for skp in jsn["path_filters"]["re_exclusion"]:
            self._skip_path.append(skp)
        if incr_scan:
            diff_file_json = os.environ.get("DIFF_FILES")
            if diff_file_json:
                print("get diff file: %s" % diff_file_json)
                with open(diff_file_json, "r") as diff_reader:
                    self._increment_files = json.load(diff_reader)

    def create_cpp_cfg(self, out_path):
        cfg = ET.parse(out_path)
        if not cfg:
            raise Exception("error load {}".format(out_path))

        for section in cfg.findall("section"):
            # update rule switch
            if section.get("name") == "Checks":
                # NOCA: invalid-name(设计如此)
                for id in section:
                    for subid in id:
                        if subid.get("name") in self._rules:
                            subid.set("value", "1")
                        else:
                            subid.set("value", "0")
            # update filter path
            # codecc use .*, tscancode use *
            elif section.get("name") == "PathToIgnore":
                for filter in self._skip_path:
                    normal_filter = filter.replace(".*", "*")
                    if len(normal_filter) >= 2:
                        ele = ET.Element("path")
                        ele.set("name", normal_filter)
                        section.append(ele)

        # write back
        with open(out_path, "wb") as out_writer:
            out_writer.write(ET.tostring(cfg.getroot(), encoding="utf-8", method="xml"))
            return

        raise Exception("Error create {}".format(out_path))

    def create_csharp_cfg(self, out_path):
        cfg = ET.parse(out_path)
        if not cfg:
            raise Exception("error load {}".format(out_path))
        for subid in cfg.findall("subid"):
            if subid.get("name") in self._rules:
                subid.set("isopen", "1")
            else:
                subid.set("isopen", "0")
        with open(out_path, "wb") as out_writer:
            out_writer.write(ET.tostring(cfg.getroot(), encoding="utf-8", method="xml"))

        # write filter.ini
        with open(WKDIR + "/filter.ini", "w") as filter_writer:
            for filter in self._skip_path:
                normal_filter = filter.replace(".*", "")
                if len(normal_filter) >= 2:
                    filter_writer.write(normal_filter)
                    filter_writer.write("\n")

    def create_lua_cfg(self, out_path):
        cfg = ET.parse(out_path)
        if not cfg:
            raise Exception("error load {}".format(out_path))
        for section in cfg.findall("section"):
            if section.get("name") == "Checks":
                # NOCA: invalid-name(设计如此)
                for id in section:
                    for subid in id:
                        subid.set("value", "1" if subid.get("name") in self._rules else "0")
            elif section.get("name") == "PathToIgnore":
                for filter in self._skip_path:
                    normal_filter = filter.replace(".*", "*")
                    if len(normal_filter) >= 2:
                        ele = ET.Element("path")
                        ele.set("name", normal_filter)
                        section.append(ele)

        with open(out_path, "wb") as out_writer:
            out_writer.write(ET.tostring(cfg.getroot(), encoding="utf-8", method="xml"))


def run_tsc_cpp(input, output):
    cmd = "cd {} && ./TscCpp/tscancode --xml -j4 '{}' 2>'{}'".format(WKDIR, input, output)
    print(cmd)
    return os.system(cmd)


def run_tsc_csharp(input, output):
    cmd = "cd {} && ./TscLua/tsccs --xml '{}' 2>'{}'".format(WKDIR, input, output)
    print(cmd)
    return os.system(cmd)


def run_tsc_lua(input, output):
    cmd = "cd {} && ./TscSharp/tsclua --xml '{}' 2>'{}'".format(WKDIR, input, output)
    print(cmd)
    return os.system(cmd)


class CmdInfo:
    def __init__(self):
        self.input = False
        self.output = False
        # NOCA: invalid-name(设计如此)
        self.toolName = False

    # NOCA: invalid-name(设计如此)
    def Parse(self, argv):
        args = len(argv)
        # NOCA: invalid-name(设计如此)
        ii = 1
        # NOCA: invalid-name(设计如此)
        while ii < args:
            if argv[ii].startswith("--json="):
                if len(argv[ii]) <= 7:
                    print("more arg expected after --json/input")
                    return False
                self.input = argv[ii][7:]
            elif argv[ii].startswith("--output="):
                if ii >= args:
                    print("more arg expected after --output")
                    return False
                self.output = argv[ii][9:]
            else:
                # NOCA: invalid-name(设计如此)
                self.toolName = argv[ii]
            # NOCA: invalid-name(设计如此)
            ii += 1

        return True


def main(argv):
    cmd_info = CmdInfo()
    input = InputInfo()
    input.parse_input()
    result_path = ""

    if cmd_info.toolName == "cpp":
        # input.create_cpp_cfg(WKDIR + "/cfg/cfg.xml")
        result_path = os.path.join(input._result_dir, "cpp_result.xml")
        run_tsc_cpp(input._scan_path, result_path)
    elif cmd_info.toolName == "csharp":
        # input.create_csharp_cfg(WKDIR + "/cfg/rule.xml")
        result_path = os.path.join(input._result_dir, "csharp_result.xml")
        run_tsc_csharp(input._scan_path, result_path)
    elif cmd_info.toolName == "lua":
        # input.create_lua_cfg(WKDIR + "/cfg/lua_cfg.xml")
        result_path = os.path.join(input._result_dir, "lua_result.xml")
        run_tsc_lua(input._scan_path, result_path)
    else:
        print("unknown tool name")

    issues = []
    if not os.path.exists(result_path):
        print("工具执行错误未生成result")
    else:
        result_tree = ET.parse(result_path)
        root = result_tree.getroot()
        for error in root:
            error_attr = error.attrib
            path = error_attr["file"]
            if not path:
                continue
            rule = error_attr["subid"]
            if not rule or rule not in input._rules:
                continue
            issues.append(
                {
                    "path": path,
                    "rule": rule,
                    "line": int(error_attr.get("line", "0")),
                    "column": "1",
                    "msg": error_attr.get("msg", ""),
                }
            )

    with open(os.path.join(input._result_dir, "result.json"), "w") as result_writer:
        json.dump(issues, result_writer, indent=2)


if __name__ == "__main__":
    print(WKDIR)
    main(sys.argv)