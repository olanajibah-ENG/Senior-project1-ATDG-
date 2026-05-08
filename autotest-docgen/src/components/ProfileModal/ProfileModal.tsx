import React, { useState, useRef, useEffect, type ChangeEvent } from 'react';
import { Camera, X, Save, User, GraduationCap, MapPin, BookOpen, Calendar, Trash2 } from 'lucide-react';

interface ProfileModalProps {
    isOpen: boolean;
    onClose: () => void;
    user: any;
    onSave: (profileData: any) => void;
    isLoading: boolean;
}

const ProfileModal: React.FC<ProfileModalProps> = ({
    isOpen,
    onClose,
    user,
    onSave,
    isLoading
}) => {
    const [profileData, setProfileData] = useState({
        firstName: user?.firstName || user?.username || '',
        lastName: user?.lastName || '',
        email: user?.email || '',
        studentId: user?.studentId || '',
        university: user?.university || '',
        major: user?.major || '',
        academicYear: user?.academicYear || '',
        profileImage: user?.profileImage || null
    });

    const [previewImage, setPreviewImage] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Load saved profile data when modal opens or user changes
    useEffect(() => {
        if (isOpen) {
            // Get saved profile data from localStorage
            const savedProfile = localStorage.getItem('userProfile');
            let savedData: any = {};
            if (savedProfile) {
                try {
                    savedData = JSON.parse(savedProfile);
                } catch (error) {
                    console.error('Error parsing saved profile data:', error);
                }
            }

            // Merge user data with saved data, prioritizing saved data
            setProfileData({
                firstName: savedData.firstName || user?.firstName || user?.username || '',
                lastName: savedData.lastName || user?.lastName || '',
                email: user?.email || '',
                studentId: savedData.studentId || user?.studentId || '',
                university: savedData.university || user?.university || '',
                major: savedData.major || user?.major || '',
                academicYear: savedData.academicYear || user?.academicYear || '',
                profileImage: savedData.profileImage || user?.profileImage || null
            });

            // Set preview image if available and valid
            if (savedData.profileImage) {
                if (typeof savedData.profileImage === 'string') {
                    setPreviewImage(savedData.profileImage);
                }
            } else if (user?.profileImage) {
                if (typeof user.profileImage === 'string') {
                    setPreviewImage(user.profileImage);
                }
            }
        }
    }, [isOpen, user]);

    const handleInputChange = (e: ChangeEvent<HTMLInputElement> | any) => {
        const { name, value } = e.target;
        setProfileData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleImageChange = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (file.size > 5 * 1024 * 1024) { // 5MB limit
                alert('Image size should be less than 5MB');
                return;
            }

            const reader = new FileReader();
            reader.onloadend = () => {
                const result = reader.result as string;
                setPreviewImage(result);
                setProfileData(prev => ({
                    ...prev,
                    profileImage: result // Save as base64 string
                }));
            };
            reader.readAsDataURL(file);
        }
    };

    const handleImageUpload = () => {
        fileInputRef.current?.click();
    };

    const handleDeletePhoto = () => {
        setPreviewImage(null);
        setProfileData(prev => ({
            ...prev,
            profileImage: null
        }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave(profileData);
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content profile-modal" onClick={(e) => e.stopPropagation()}>
                {/* Header */}
                <div className="profile-modal-header">
                    <h2>Profile Settings</h2>
                    <button
                        className="close-btn"
                        onClick={onClose}
                        title="Close"
                    >
                        <X size={24} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="profile-form">
                    {/* Profile Image Section */}
                    <div className="profile-image-section">
                        <div className="profile-image-container">
                            <div className="profile-image-wrapper">
                                {previewImage ? (
                                    <img
                                        src={previewImage}
                                        alt="Profile"
                                        className="profile-image"
                                    />
                                ) : profileData.profileImage ? (
                                    <img
                                        src={profileData.profileImage}
                                        alt="Profile"
                                        className="profile-image"
                                    />
                                ) : (
                                    <div className="profile-image-placeholder">
                                        <User size={80} />
                                    </div>
                                )}
                            </div>
                            <div className="photo-buttons-container">
                                <button
                                    type="button"
                                    className="upload-photo-btn"
                                    onClick={handleImageUpload}
                                    title="Upload new photo"
                                >
                                    <Camera size={20} />
                                    Upload new photo
                                </button>
                                {/* Show delete button when there's any image (preview, current, or user profile image) */}
                                {(previewImage || profileData.profileImage || user?.profileImage) && (
                                    <button
                                        type="button"
                                        className="delete-photo-btn"
                                        onClick={handleDeletePhoto}
                                        title="Delete photo"
                                    >
                                        <Trash2 size={20} />
                                        Delete photo
                                    </button>
                                )}
                            </div>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/*"
                                onChange={handleImageChange}
                                style={{ display: 'none' }}
                            />
                        </div>
                    </div>

                    {/* Personal Information */}
                    <div className="form-section">
                        <h3 className="section-title">Personal Information</h3>

                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="firstName">
                                    First Name *
                                </label>
                                <input
                                    type="text"
                                    id="firstName"
                                    name="firstName"
                                    value={profileData.firstName}
                                    onChange={handleInputChange}
                                    required
                                    placeholder="Enter your first name"
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="lastName">
                                    Last Name *
                                </label>
                                <input
                                    type="text"
                                    id="lastName"
                                    name="lastName"
                                    value={profileData.lastName}
                                    onChange={handleInputChange}
                                    required
                                    placeholder="Enter your last name"
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label htmlFor="email">
                                Email
                            </label>
                            <input
                                type="email"
                                id="email"
                                name="email"
                                value={profileData.email}
                                readOnly
                                className="readonly-input"
                                placeholder="your.email@example.com"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="studentId">
                                <GraduationCap size={16} />
                                Student ID
                            </label>
                            <input
                                type="text"
                                id="studentId"
                                name="studentId"
                                value={profileData.studentId}
                                onChange={handleInputChange}
                                placeholder="Enter your student ID"
                            />
                        </div>
                    </div>

                    {/* Academic Information */}
                    <div className="form-section">
                        <h3 className="section-title">
                            <BookOpen size={18} />
                            Academic Information
                        </h3>

                        <div className="form-group">
                            <label htmlFor="university">
                                <MapPin size={16} />
                                University
                            </label>
                            <select
                                id="university"
                                name="university"
                                value={profileData.university}
                                onChange={handleInputChange}
                            >
                                <option value="">Select University</option>
                                <option value="Damascus University">Damascus University</option>
                                <option value="Aleppo Abdulaziz University">Aleppo University</option>
                                <option value="Syrian private University">Syrian private University </option>
                                <option value="Homs University">Homs University</option>
                                <option value="Hama University">Hama University</option>
                                <option value="IUST University">IUST University</option>
                                <option value="AIU University">AIU University</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label htmlFor="major">
                                    <BookOpen size={16} />
                                    Major
                                </label>
                                <select
                                    id="major"
                                    name="major"
                                    value={profileData.major}
                                    onChange={handleInputChange}
                                >
                                    <option value="">Select Major</option>
                                    <option value="Computer Science">Computer Science</option>
                                    <option value="Information Technology">Information Technology</option>
                                    <option value="Software Engineering">Software Engineering</option>
                                    <option value="Computer Engineering">Computer Engineering</option>
                                    <option value="Information Systems">Information Systems</option>
                                    <option value="Cybersecurity">Cybersecurity</option>
                                    <option value="Data Science">Data Science</option>
                                    <option value="Artificial Intelligence">Artificial Intelligence</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label htmlFor="academicYear">
                                    <Calendar size={16} />
                                    Academic Year
                                </label>
                                <select
                                    id="academicYear"
                                    name="academicYear"
                                    value={profileData.academicYear}
                                    onChange={handleInputChange}
                                >
                                    <option value="">Select Year</option>
                                    <option value="First Year">First Year</option>
                                    <option value="Second Year">Second Year</option>
                                    <option value="Third Year">Third Year</option>
                                    <option value="Fourth Year">Fourth Year</option>
                                    <option value="Fifth Year">Fifth Year</option>
                                    <option value="Graduate Student">Graduate Student</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="profile-modal-actions">
                        <button
                            type="button"
                            className="btn-secondary"
                            onClick={onClose}
                            disabled={isLoading}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="btn-primary"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <div className="loading-spinner-small"></div>
                                    Saving...
                                </>
                            ) : (
                                <>
                                    <Save size={16} />
                                    Save Changes
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ProfileModal;
