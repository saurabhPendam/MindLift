// Doctor Consultation JavaScript with Jitsi Meet Integration

let jitsiApi = null;

function startVideoCall(doctorName) {
    // Generate a unique room name
    const roomName = `mindlift-${Date.now()}-${Math.random().toString(36).substring(7)}`;
    
    // Create modal with Jitsi
    const modal = new bootstrap.Modal(document.getElementById('videoCallModal'));
    document.getElementById('doctorName').textContent = `Video Call with ${doctorName}`;
    
    // Show modal first
    modal.show();
    
    // Wait for modal to be shown, then initialize Jitsi
    setTimeout(() => {
        initializeJitsiMeet(roomName, doctorName);
    }, 500);
}

function initializeJitsiMeet(roomName, doctorName) {
    const domain = 'meet.jit.si';
    const container = document.getElementById('jitsiContainer');
    
    // Clear any existing instance
    if (jitsiApi) {
        jitsiApi.dispose();
        jitsiApi = null;
    }
    
    // Clear container
    container.innerHTML = '';
    
    const options = {
        roomName: roomName,
        width: '100%',
        height: 600,
        parentNode: container,
        configOverwrite: {
            startWithAudioMuted: false,
            startWithVideoMuted: false,
            enableWelcomePage: false,
            prejoinPageEnabled: false,
            disableDeepLinking: true,
        },
        interfaceConfigOverwrite: {
            TOOLBAR_BUTTONS: [
                'microphone', 'camera', 'closedcaptions', 'desktop', 'fullscreen',
                'fodeviceselection', 'hangup', 'profile', 'chat', 'recording',
                'livestreaming', 'etherpad', 'sharedvideo', 'settings', 'raisehand',
                'videoquality', 'filmstrip', 'feedback', 'stats', 'shortcuts',
                'tileview', 'videobackgroundblur', 'download', 'help', 'mute-everyone'
            ],
            SHOW_JITSI_WATERMARK: false,
            SHOW_WATERMARK_FOR_GUESTS: false,
            DEFAULT_BACKGROUND: '#f5f7fa',
            DISABLE_JOIN_LEAVE_NOTIFICATIONS: true,
        },
        userInfo: {
            displayName: 'Patient'
        }
    };
    
    try {
        jitsiApi = new JitsiMeetExternalAPI(domain, options);
        
        // Event listeners
        jitsiApi.addEventListener('videoConferenceJoined', () => {
            console.log('Video conference joined');
            showNotification('Video call connected!', 'success');
        });
        
        jitsiApi.addEventListener('videoConferenceLeft', () => {
            console.log('Video conference left');
            const modal = bootstrap.Modal.getInstance(document.getElementById('videoCallModal'));
            if (modal) modal.hide();
        });
        
        jitsiApi.addEventListener('readyToClose', () => {
            if (jitsiApi) {
                jitsiApi.dispose();
                jitsiApi = null;
            }
        });
        
    } catch (error) {
        console.error('Error initializing Jitsi:', error);
        showNotification('Error starting video call. Please try again.', 'danger');
    }
}

function viewProfile(doctorName) {
    const profiles = {
        'Dr. Sarah Johnson': {
            specialization: 'Clinical Psychologist',
            experience: '15+ years',
            education: 'Ph.D. in Clinical Psychology, Harvard University',
            expertise: ['Anxiety', 'Depression', 'Cognitive Behavioral Therapy', 'Trauma Recovery'],
            languages: ['English', 'Spanish'],
            rating: 4.9,
            reviews: 250
        },
        'Dr. Michael Chen': {
            specialization: 'Psychiatrist',
            experience: '12+ years',
            education: 'M.D. in Psychiatry, Johns Hopkins University',
            expertise: ['Mood Disorders', 'PTSD', 'Medication Management', 'Bipolar Disorder'],
            languages: ['English', 'Mandarin'],
            rating: 4.8,
            reviews: 180
        },
        'Dr. Emily Parker': {
            specialization: 'Marriage & Family Therapist',
            experience: '10+ years',
            education: 'M.A. in Marriage and Family Therapy, UCLA',
            expertise: ['Relationship Counseling', 'Family Therapy', 'Trauma Recovery', 'Communication'],
            languages: ['English', 'French'],
            rating: 5.0,
            reviews: 95
        },
        'Dr. James Rodriguez': {
            specialization: 'Addiction Specialist',
            experience: '18+ years',
            education: 'Ph.D. in Clinical Psychology, Stanford University',
            expertise: ['Substance Abuse', 'Addiction Recovery', 'Dual Diagnosis', 'Group Therapy'],
            languages: ['English', 'Spanish', 'Portuguese'],
            rating: 4.7,
            reviews: 120
        }
    };
    
    const profile = profiles[doctorName];
    
    if (!profile) {
        showNotification('Profile not found', 'warning');
        return;
    }
    
    const modalHTML = `
        <div class="modal fade" id="profileModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title fw-bold">${doctorName}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-4 text-center">
                                <div class="doctor-profile-image mb-3">
                                    <div style="width: 150px; height: 150px; margin: 0 auto; border-radius: 50%; background: linear-gradient(135deg, #7c9cbf, #9d9cb3); display: flex; align-items: center; justify-content: center; font-size: 3rem; color: white;">
                                        ${doctorName.split(' ').map(n => n[0]).join('')}
                                    </div>
                                </div>
                                <h6 class="fw-bold">${profile.specialization}</h6>
                                <div class="mb-3">
                                    <i class="fas fa-star" style="color: #ffb74d;"></i> ${profile.rating} 
                                    <span class="text-muted">(${profile.reviews} reviews)</span>
                                </div>
                            </div>
                            <div class="col-md-8">
                                <h6 class="fw-bold mb-3">About</h6>
                                <p><strong>Experience:</strong> ${profile.experience}</p>
                                <p><strong>Education:</strong> ${profile.education}</p>
                                
                                <h6 class="fw-bold mb-2 mt-3">Areas of Expertise</h6>
                                <div class="d-flex flex-wrap gap-2 mb-3">
                                    ${profile.expertise.map(exp => `
                                        <span class="badge" style="background: rgba(124, 156, 191, 0.2); color: #7c9cbf; padding: 0.5rem 1rem; font-weight: 500;">
                                            ${exp}
                                        </span>
                                    `).join('')}
                                </div>
                                
                                <h6 class="fw-bold mb-2 mt-3">Languages</h6>
                                <p>${profile.languages.join(', ')}</p>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" onclick="startVideoCall('${doctorName}'); bootstrap.Modal.getInstance(document.getElementById('profileModal')).hide();">
                            <i class="fas fa-video me-2"></i>Start Video Call
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing profile modal if any
    const existingModal = document.getElementById('profileModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('profileModal'));
    modal.show();
}

function scheduleAppointment(doctorName) {
    const modalHTML = `
        <div class="modal fade" id="scheduleModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title fw-bold">Schedule Appointment</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="appointmentForm">
                            <div class="mb-3">
                                <label class="form-label">Doctor</label>
                                <input type="text" class="form-control" value="${doctorName}" readonly>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Appointment Date</label>
                                <input type="date" class="form-control" id="appointmentDate" required min="${new Date().toISOString().split('T')[0]}">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Preferred Time</label>
                                <select class="form-select" id="appointmentTime" required>
                                    <option value="">Select time...</option>
                                    <option value="09:00">9:00 AM</option>
                                    <option value="10:00">10:00 AM</option>
                                    <option value="11:00">11:00 AM</option>
                                    <option value="14:00">2:00 PM</option>
                                    <option value="15:00">3:00 PM</option>
                                    <option value="16:00">4:00 PM</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Reason for Consultation (Optional)</label>
                                <textarea class="form-control" id="appointmentReason" rows="3"></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="submitAppointment('${doctorName}')">
                            <i class="fas fa-calendar-check me-2"></i>Schedule
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('scheduleModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('scheduleModal'));
    modal.show();
}

function submitAppointment(doctorName) {
    const date = document.getElementById('appointmentDate').value;
    const time = document.getElementById('appointmentTime').value;
    const reason = document.getElementById('appointmentReason').value;
    
    if (!date || !time) {
        showNotification('Please select date and time', 'warning');
        return;
    }
    
    // In production, send this to your backend
    const appointmentData = {
        doctor: doctorName,
        date: date,
        time: time,
        reason: reason
    };
    
    console.log('Appointment scheduled:', appointmentData);
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('scheduleModal'));
    modal.hide();
    
    // Show success message
    showNotification(`Appointment scheduled with ${doctorName} on ${date} at ${time}`, 'success');
    
    // You can send this to backend:
    // fetch('/api/schedule-appointment/', {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'application/json',
    //         'X-CSRFToken': getCookie('csrftoken')
    //     },
    //     body: JSON.stringify(appointmentData)
    // });
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} position-fixed top-0 start-50 translate-middle-x mt-3`;
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Cleanup on modal close
document.addEventListener('DOMContentLoaded', () => {
    const videoModal = document.getElementById('videoCallModal');
    
    if (videoModal) {
        videoModal.addEventListener('hidden.bs.modal', () => {
            // Cleanup Jitsi
            if (jitsiApi) {
                jitsiApi.dispose();
                jitsiApi = null;
            }
            
            // Clear container
            const container = document.getElementById('jitsiContainer');
            if (container) {
                container.innerHTML = '';
            }
            
            console.log('Video call ended');
        });
    }
});