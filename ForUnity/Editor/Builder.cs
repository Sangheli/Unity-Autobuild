using UnityEditor;
using UnityEngine;
using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Text.RegularExpressions;

public class Builder
{
    private class BuildParam
    {
        public BuildTarget BuildTarget;
        public string Folder;
        public string Extension = string.Empty;
        public bool UseName = true;
        public string GetExeName() => !UseName ? null : $"{GetName()}{Extension}";
        
        private static string GetName() => 
            Regex.Replace(Application.productName, @"[^a-zA-Z0-9]", "").ToLower();
    }

    private static readonly Dictionary<string, BuildParam> BuildParams = new()
    {
        { "Android", new BuildParam { BuildTarget = BuildTarget.Android, Folder = "androidBuild", Extension = ".apk" } },
        { "Linux64", new BuildParam { BuildTarget = BuildTarget.StandaloneLinux64, Folder = "linux_build"} },
        { "OSX",     new BuildParam { BuildTarget = BuildTarget.StandaloneOSX, Folder = "mac_build"} },
        { "Win64",   new BuildParam { BuildTarget = BuildTarget.StandaloneWindows64, Folder = "pc_build", Extension = ".exe" } },
        { "WebGL",   new BuildParam { BuildTarget = BuildTarget.WebGL, Folder = "webgl_build", UseName = false } },
    };

    private const string BuildTargetParam = "-buildTarget";

    [MenuItem("Build/Build Android")]
    public static void BuildAndroid() => BuildWithParam(BuildTarget.Android);

    [MenuItem("Build/Build Linux")]
    public static void BuildLinux() => BuildWithParam(BuildTarget.StandaloneLinux64);
    
    [MenuItem("Build/Build Mac")]
    public static void BuildMac() => BuildWithParam(BuildTarget.StandaloneOSX);
    
    [MenuItem("Build/Build Win")]
    public static void BuildWin() => BuildWithParam(BuildTarget.StandaloneWindows64);
    
    [MenuItem("Build/Build Webgl")]
    public static void BuildWebgl() => BuildWithParam(BuildTarget.WebGL);

    public static void Build() => BuildWithParam(GetPlatform(Environment.GetCommandLineArgs()));

    private static void BuildWithParam(string buildTarget)
    {
        if (string.IsNullOrEmpty(buildTarget) || !BuildParams.TryGetValue(buildTarget, out var param))
        {
            Debug.LogError($"[UnifiedBuilder] Неизвестная платформа: [{buildTarget}]. Используйте -buildTarget <BuildTarget>");
            return;
        }

        BuildWithParam(param);
    }

    private static void BuildWithParam(BuildTarget buildTarget)
    {
        var param = BuildParams.Values.FirstOrDefault(x => x.BuildTarget == buildTarget);
        if (param == null)
            Debug.LogError($"[UnifiedBuilder] Неизвестная платформа: {buildTarget}. Используйте -buildTarget <BuildTarget>");

        BuildWithParam(param);
    }

    private static void BuildWithParam(BuildParam param)
    {
        Debug.Log($"Build Start: {param.BuildTarget}");
        Build(param.BuildTarget, param.Folder, param.GetExeName());
        Debug.Log($"Build Done: {param.BuildTarget}");
    }

    private static void Build(BuildTarget buildTarget, string buildFolder, string exeName = null)
    {
        if (Directory.Exists(buildFolder)) 
            Directory.Delete(buildFolder, true);
        
        Directory.CreateDirectory(buildFolder);
        
        var finalPath = exeName == null ? buildFolder : Path.Combine(buildFolder, exeName);

        BuildPipeline.BuildPlayer
        (
            GetEnabledScenes(),
            finalPath,
            buildTarget,
            GetBuildOptions()
        );
    }
    
    private static string[] GetEnabledScenes()
    {
        return EditorBuildSettings.scenes
            .Where(scene => scene.enabled)
            .Select(scene => scene.path)
            .ToArray();
    }
    
    private static BuildOptions GetBuildOptions()
    {
        return BuildOptions.None;
        return BuildOptions.Development | BuildOptions.AllowDebugging;
    }
    
    private static string GetPlatform(string[] args)
    {
        for (var index = 0; index < args.Length; index++)
        {
            if (args[index] == BuildTargetParam)
                return args[index + 1];
        }

        return null;
    }
} 