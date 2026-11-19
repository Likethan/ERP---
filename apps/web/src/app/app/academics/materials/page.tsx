"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { teachingService } from "@/services/teaching.service";
import { CourseStudyMaterial, MaterialFileType } from "@/types/teaching";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  FileText,
  Upload,
  Plus,
  BookOpen,
  Download,
  ExternalLink,
  Layers,
  Search,
  Filter,
  CheckCircle2,
  FileCode,
  FileSpreadsheet,
  Film,
  Sparkles,
} from "lucide-react";

export default function StudyMaterialsPage() {
  const { user, activePersona } = useAuth();
  const { showToast } = useToast();

  const userRole = activePersona?.role || user?.roles?.[0]?.name || "STUDENT";
  const isFaculty =
    userRole === "FACULTY" ||
    userRole === "HOD" ||
    userRole === "ADMIN" ||
    userRole === "SUPER_ADMIN";

  const [loading, setLoading] = useState(true);
  const [materials, setMaterials] = useState<CourseStudyMaterial[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>("co-cs301-a");
  const [selectedUnit, setSelectedUnit] = useState<number>(0);
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Upload Modal
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [formData, setFormData] = useState({
    courseOfferingId: "co-cs301-a",
    courseCode: "CS301",
    courseName: "Data Structures & Algorithms",
    section: "A",
    unitNumber: 1,
    title: "",
    description: "",
    materialType: "PDF" as MaterialFileType,
    fileUrl: "",
    fileName: "",
    fileSize: "2.5 MB",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await teachingService.getStudyMaterials({
        courseOfferingId: selectedCourse,
        unitNumber: selectedUnit,
        materialType: selectedType,
      });
      if (res.success) {
        setMaterials(res.data);
      }
    } catch (err) {
      console.error(err);
      showToast({
        type: "error",
        title: "Error",
        message: "Failed to load materials.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCourse, selectedUnit, selectedType]);

  const filteredMaterials = useMemo(() => {
    if (!searchQuery.trim()) return materials;
    const q = searchQuery.toLowerCase();
    return materials.filter(
      (m) =>
        m.title.toLowerCase().includes(q) ||
        m.description.toLowerCase().includes(q) ||
        m.fileName.toLowerCase().includes(q),
    );
  }, [materials, searchQuery]);

  const totalDownloads = useMemo(
    () => materials.reduce((acc, m) => acc + m.downloadCount, 0),
    [materials],
  );

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      showToast({
        type: "error",
        title: "Validation Error",
        message: "Title is required.",
      });
      return;
    }
    try {
      setUploading(true);
      const res = await teachingService.uploadStudyMaterial({
        courseOfferingId: formData.courseOfferingId,
        courseCode: formData.courseCode,
        courseName: formData.courseName,
        section: formData.section,
        unitNumber: Number(formData.unitNumber),
        title: formData.title,
        description: formData.description,
        materialType: formData.materialType,
        fileUrl:
          formData.fileUrl ||
          `/assets/materials/${formData.fileName || "document.pdf"}`,
        fileName:
          formData.fileName || `${formData.title.replace(/\s+/g, "_")}.pdf`,
        fileSize: formData.fileSize || "1.8 MB",
        uploadedByFacultyId: activePersona?.id || "fac-cse-01",
        uploadedByFacultyName: activePersona?.name || "Dr. Rajesh Sharma",
      });

      if (res.success) {
        showToast({
          type: "success",
          title: "Study Material Uploaded",
          message:
            "Material published and immediately accessible by enrolled students.",
        });
        setUploadModalOpen(false);
        setFormData({
          ...formData,
          title: "",
          description: "",
          fileName: "",
          fileUrl: "",
        });
        await loadData();
      }
    } catch (err: any) {
      showToast({
        type: "error",
        title: "Upload Failed",
        message: err.message,
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (mat: CourseStudyMaterial) => {
    await teachingService.incrementMaterialDownload(mat.id);
    showToast({
      type: "success",
      title: "Downloading File",
      message: `Opening ${mat.fileName} (${mat.fileSize}).`,
    });
    setMaterials((prev) =>
      prev.map((m) =>
        m.id === mat.id ? { ...m, downloadCount: m.downloadCount + 1 } : m,
      ),
    );
  };

  const getFileIcon = (type: MaterialFileType) => {
    switch (type) {
      case "PDF":
        return <FileText className="h-5 w-5 text-rose-500" />;
      case "PPT":
        return <FileSpreadsheet className="h-5 w-5 text-amber-500" />;
      case "DOCX":
        return <FileText className="h-5 w-5 text-sky-500" />;
      case "LINK":
        return <ExternalLink className="h-5 w-5 text-emerald-500" />;
      case "VIDEO":
        return <Film className="h-5 w-5 text-purple-500" />;
      default:
        return <FileCode className="h-5 w-5 text-indigo-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-xs border-l-4 border-l-yellow-400">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-semibold text-yellow-950 border border-yellow-300 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-yellow-600" />
            Academic Content & Courseware Repository
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            Course Study Materials
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500">
            Curriculum slide decks, lecture notes, lab manuals, question banks,
            and reference links organized by course module.
          </p>
        </div>

        {isFaculty && (
          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Upload className="h-3.5 w-3.5" />}
              onClick={() => setUploadModalOpen(true)}
            >
              Upload Material
            </Button>
          </div>
        )}
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          label="Total Documents"
          value={materials.length}
          description="Handouts, slide decks, and code samples"
          variant="indigo"
          icon={<BookOpen className="h-4 w-4" />}
        />
        <StatCard
          label="Student Downloads"
          value={totalDownloads}
          description="Document reads and downloads by students"
          variant="emerald"
          icon={<Download className="h-4 w-4" />}
        />
        <StatCard
          label="Course Access"
          value="Enrolled Cohorts"
          description="Synchronized directly with student portal"
          variant="amber"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-yellow-600" />
            <select
              value={selectedCourse}
              onChange={(e) => setSelectedCourse(e.target.value)}
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
            >
              <option value="co-cs301-a">
                CS301 — Data Structures & Algorithms (Sec A)
              </option>
              <option value="co-cs501-a">
                CS501 — Compiler Design (Sec A)
              </option>
              <option value="co-cs402-b">
                CS402 — Operating Systems (Sec B)
              </option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-slate-400" />
            <select
              value={selectedUnit}
              onChange={(e) => setSelectedUnit(Number(e.target.value))}
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
            >
              <option value="0">All Syllabus Units</option>
              <option value="1">Unit 1: Linear Structures</option>
              <option value="2">Unit 2: Balanced Trees</option>
              <option value="3">Unit 3: Graph Algorithms</option>
              <option value="4">Unit 4: Hashing & Heaps</option>
              <option value="5">Unit 5: NP-Completeness</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
            >
              <option value="ALL">All File Types</option>
              <option value="PDF">PDF Documents</option>
              <option value="PPT">PowerPoint Slides</option>
              <option value="DOCX">Word Documents</option>
              <option value="LINK">External Links</option>
            </select>
          </div>
        </div>

        <div className="relative w-full lg:w-64">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
          <Input
            placeholder="Search materials..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 text-xs"
          />
        </div>
      </div>

      {/* Materials Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading ? (
          <div className="col-span-2 p-8 text-center text-xs text-slate-400">
            Loading study materials...
          </div>
        ) : filteredMaterials.length === 0 ? (
          <div className="col-span-2 p-8 text-center text-xs text-slate-400">
            No materials found matching criteria.
          </div>
        ) : (
          filteredMaterials.map((mat) => (
            <Card
              key={mat.id}
              className="hover:border-yellow-300 transition-all"
            >
              <CardContent className="p-5 flex flex-col justify-between h-full space-y-4">
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <div className="p-2 rounded-lg bg-slate-100 border border-slate-200">
                        {getFileIcon(mat.materialType)}
                      </div>
                      <div>
                        <Badge
                          variant="outline"
                          className="text-[10px] font-mono"
                        >
                          Unit {mat.unitNumber} • {mat.materialType}
                        </Badge>
                        <h3 className="text-sm font-bold text-slate-900 mt-1 leading-snug">
                          {mat.title}
                        </h3>
                      </div>
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 line-clamp-2">
                    {mat.description}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <div className="text-[11px] text-slate-500">
                    <span>{mat.fileName}</span> •{" "}
                    <span className="font-mono">{mat.fileSize}</span>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      Uploaded by {mat.uploadedByFacultyName}
                    </div>
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 px-3 text-xs flex items-center gap-1.5 border-yellow-300 bg-yellow-50/30 hover:bg-yellow-100"
                    onClick={() => handleDownload(mat)}
                  >
                    {mat.materialType === "LINK" ? (
                      <>
                        <ExternalLink className="h-3 w-3" />
                        <span>Visit</span>
                      </>
                    ) : (
                      <>
                        <Download className="h-3 w-3" />
                        <span>Download ({mat.downloadCount})</span>
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Upload Material Dialog */}
      <Dialog
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        title="Upload Course Study Material"
      >
        <form onSubmit={handleUpload} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-700">
              Document Title
            </label>
            <Input
              placeholder="e.g. Unit 3: Graph Algorithms & Flow Visualizer"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Syllabus Unit
              </label>
              <select
                value={formData.unitNumber}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    unitNumber: Number(e.target.value),
                  })
                }
                className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              >
                <option value="1">Unit 1: Linear Structures</option>
                <option value="2">Unit 2: Balanced Trees</option>
                <option value="3">Unit 3: Graph Algorithms</option>
                <option value="4">Unit 4: Hashing & Heaps</option>
                <option value="5">Unit 5: NP-Completeness</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700">
                Material Format
              </label>
              <select
                value={formData.materialType}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    materialType: e.target.value as MaterialFileType,
                  })
                }
                className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              >
                <option value="PDF">PDF Document (.pdf)</option>
                <option value="PPT">PowerPoint Slide Deck (.pptx)</option>
                <option value="DOCX">Word Document (.docx)</option>
                <option value="LINK">External Educational Link / URL</option>
                <option value="VIDEO">Video Lecture / Tutorial</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">
              Description / Topic Outline
            </label>
            <textarea
              rows={2}
              placeholder="Outline what concepts this material covers..."
              className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
            />
          </div>

          {formData.materialType === "LINK" ? (
            <div>
              <label className="text-xs font-semibold text-slate-700">
                Target URL
              </label>
              <Input
                type="url"
                placeholder="https://..."
                value={formData.fileUrl}
                onChange={(e) =>
                  setFormData({ ...formData, fileUrl: e.target.value })
                }
                required
              />
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700">
                  File Name
                </label>
                <Input
                  placeholder="CS301_LectureNotes.pdf"
                  value={formData.fileName}
                  onChange={(e) =>
                    setFormData({ ...formData, fileName: e.target.value })
                  }
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700">
                  Estimated File Size
                </label>
                <Input
                  placeholder="e.g. 4.2 MB"
                  value={formData.fileSize}
                  onChange={(e) =>
                    setFormData({ ...formData, fileSize: e.target.value })
                  }
                />
              </div>
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <Button
              variant="ghost"
              size="sm"
              type="button"
              onClick={() => setUploadModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              type="submit"
              disabled={uploading}
            >
              {uploading ? "Publishing..." : "Upload & Publish to Class"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
