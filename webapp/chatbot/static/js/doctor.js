// Doctor Consultation JavaScript with Jitsi Meet Integration - COMPLETE FIXED VERSION
// File: chatbot/static/js/doctor.js

let jitsiApi = null;
let currentRoomName = null;

function startVideoCall(doctorName) {
    console.log('Starting video call with:', doctorName);
    
    // Check if Jitsi API is loaded
    if (typeof JitsiMeetExternalAPI === 'undefined') {
        showNotification('Jitsi Meet is not loaded. Please refresh the page and try again.', 'danger');
        console.error('JitsiMeetExternalAPI is not defined');
        return;
    }
    
    // Generate a unique room name
    currentRoomName = `mindlift-${Date.now()}-${Math.random().toString(36).substring(7)}`;
    console.log('Room name:', currentRoomName);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('videoCallModal'));
    document.getElementById('doctorName').textContent = `Video Call with ${doctorName}`;
    modal.show();
    
    // Initialize Jitsi after modal is shown
    setTimeout(() => {
        initializeJitsiMeet(currentRoomName, doctorName);
    }, 500);
}

function initializeJitsiMeet(roomName, doctorName) {
    const domain = 'meet.jit.si';
    const container = document.getElementById('jitsiContainer');
    
    console.log('Initializing Jitsi Meet...');
    console.log('Domain:', domain);
    console.log('Room:', roomName);
    
    // Clear any existing instance
    if (jitsiApi) {
        try {
            console.log('Disposing previous Jitsi instance');
            jitsiApi.dispose();
        } catch (e) {
            console.log('Error disposing previous Jitsi instance:', e);
        }
        jitsiApi = null;
    }
    
    // Clear container
    container.innerHTML = '';
    
    const options = {
        roomName: roomName,
        width: '100%',
        height: '100%',
        parentNode: container,
        configOverwrite: {
            startWithAudioMuted: false,
            startWithVideoMuted: false,
            enableWelcomePage: false,
            prejoinPageEnabled: true,  // Show pre-join screen for device selection
            disableDeepLinking: true,
            enableNoisyMicDetection: true,
            resolution: 720,
            constraints: {
                video: {
                    height: {
                        ideal: 720,
                        max: 720,
                        min: 240
                    }
                }
            },
            // CRITICAL: Disable features that might cause issues
            disableThirdPartyRequests: false,
            enableP2P: true,
            p2p: {
                enabled: true
            }
        },
        interfaceConfigOverwrite: {
            TOOLBAR_BUTTONS: [
                'microphone', 'camera', 'closedcaptions', 'desktop', 'fullscreen',
                'fodeviceselection', 'hangup', 'profile', 'chat', 'recording',
                'etherpad', 'sharedvideo', 'settings', 'raisehand',
                'videoquality', 'filmstrip', 'stats', 'shortcuts',
                'tileview', 'videobackgroundblur', 'help'
            ],
            SHOW_JITSI_WATERMARK: false,
            SHOW_WATERMARK_FOR_GUESTS: false,
            DEFAULT_BACKGROUND: '#f5f7fa',
            DISABLE_JOIN_LEAVE_NOTIFICATIONS: true,
            SHOW_BRAND_WATERMARK: false,
            SHOW_CHROME_EXTENSION_BANNER: false,
            MOBILE_APP_PROMO: false,
        },
        userInfo: {
            displayName: 'Patient',
            email: ''
        }
    };
    
    try {
        console.log('Creating JitsiMeetExternalAPI instance...');
        jitsiApi = new JitsiMeetExternalAPI(domain, options);
        
        // Event listeners
        jitsiApi.addEventListener('videoConferenceJoined', (e) => {
            console.log('✅ Video conference joined', e);
            showNotification(`Connected to video call with ${doctorName}`, 'success');
        });
        
        jitsiApi.addEventListener('videoConferenceLeft', () => {
            console.log('👋 Video conference left');
            const modal = bootstrap.Modal.getInstance(document.getElementById('videoCallModal'));
            if (modal) {
                modal.hide();
            }
            showNotification('Call ended', 'info');
        });
        
        jitsiApi.addEventListener('readyToClose', () => {
            console.log('🔚 Ready to close');
            if (jitsiApi) {
                jitsiApi.dispose();
                jitsiApi = null;
            }
        });
        
        jitsiApi.addEventListener('participantJoined', (participant) => {
            console.log('👤 Participant joined:', participant);
            showNotification('Someone joined the call', 'info');
        });
        
        jitsiApi.addEventListener('participantLeft', (participant) => {
            console.log('👋 Participant left:', participant);
        });
        
        // Error handling
        jitsiApi.addEventListener('errorOccurred', (error) => {
            console.error('❌ Jitsi error:', error);
            showNotification('An error occurred during the call. Please try again.', 'danger');
        });
        
        // Device list changed (useful for debugging)
        jitsiApi.addEventListener('deviceListChanged', (devices) => {
            console.log('📱 Device list changed:', devices);
        });
        
        console.log('✅ Jitsi Meet initialized successfully');
        
    } catch (error) {
        console.error('❌ Error initializing Jitsi:', error);
        showNotification('Error starting video call. Please check your connection and try again.', 'danger');
        
        // Show fallback message
        container.innerHTML = `
            <div class="alert alert-danger m-4">
                <h5><i class="fas fa-exclamation-triangle me-2"></i>Could not start video call</h5>
                <p class="mb-3">Please ensure:</p>
                <ul>
                    <li>You have a stable internet connection</li>
                    <li>Camera and microphone permissions are granted</li>
                    <li>Your browser supports WebRTC (Chrome, Firefox, Safari, Edge)</li>
                    <li>Pop-ups are not blocked</li>
                    <li>You're using HTTPS (required for camera/microphone access)</li>
                </ul>
                <button class="btn btn-primary" onclick="initializeJitsiMeet('${roomName}', '${doctorName}')">
                    <i class="fas fa-redo me-2"></i>Try Again
                </button>
                <button class="btn btn-secondary ms-2" onclick="checkPermissions()">
                    <i class="fas fa-check me-2"></i>Check Permissions
                </button>
            </div>
        `;
    }
}

// Check camera and microphone permissions
async function checkPermissions() {
    console.log('Checking camera and microphone permissions...');
    
    try {
        // Request permissions
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: true, 
            audio: true 
        });
        
        console.log('✅ Permissions granted');
        showNotification('Camera and microphone permissions are granted!', 'success');
        
        // Stop the stream
        stream.getTracks().forEach(track => track.stop());
        
        // Show available devices
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(d => d.kind === 'videoinput');
        const audioDevices = devices.filter(d => d.kind === 'audioinput');
        
        console.log('Video devices:', videoDevices);
        console.log('Audio devices:', audioDevices);
        
        showNotification(
            `Found ${videoDevices.length} camera(s) and ${audioDevices.length} microphone(s). You're ready for video calls!`,
            'success'
        );
        
    } catch (error) {
        console.error('❌ Permission error:', error);
        
        let errorMessage = 'Could not access camera/microphone. ';
        
        if (error.name === 'NotAllowedError') {
            errorMessage += 'Please allow camera and microphone access in your browser settings.';
        } else if (error.name === 'NotFoundError') {
            errorMessage += 'No camera or microphone found. Please connect a device.';
        } else if (error.name === 'NotReadableError') {
            errorMessage += 'Camera/microphone is already in use by another application.';
        } else {
            errorMessage += error.message;
        }
        
        showNotification(errorMessage, 'danger');
    }
}

function viewProfile(doctorName) {
    const profiles = {
        'Dr. Sarah Johnson': {
            specialization: 'Clinical Psychologist',
            experience: '15+ years',
            education: 'Ph.D. in Clinical Psychology, Harvard University',
            expertise: ['Anxiety Disorders', 'Depression', 'Cognitive Behavioral Therapy', 'Trauma Recovery', 'Stress Management'],
            languages: ['English', 'Spanish'],
            rating: 4.9,
            reviews: 250,
            availability: 'Mon-Fri: 9 AM - 6 PM',
            bio: 'Dr. Johnson specializes in evidence-based treatments for anxiety and depression. She uses CBT and mindfulness techniques to help clients develop coping strategies.'
        },
        'Dr. Michael Chen': {
            specialization: 'Psychiatrist',
            experience: '12+ years',
            education: 'M.D. in Psychiatry, Johns Hopkins University',
            expertise: ['Mood Disorders', 'PTSD', 'Medication Management', 'Bipolar Disorder', 'Anxiety'],
            languages: ['English', 'Mandarin'],
            rating: 4.8,
            reviews: 180,
            availability: 'Tue-Sat: 10 AM - 7 PM',
            bio: 'Dr. Chen combines medication management with psychotherapy to provide comprehensive treatment for mental health conditions.'
        },
        'Dr. Emily Parker': {
            specialization: 'Marriage & Family Therapist',
            experience: '10+ years',
            education: 'M.A. in Marriage and Family Therapy, UCLA',
            expertise: ['Relationship Counseling', 'Family Therapy', 'Trauma Recovery', 'Communication Skills', 'Couples Therapy'],
            languages: ['English', 'French'],
            rating: 5.0,
            reviews: 95,
            availability: 'Mon-Thu: 1 PM - 8 PM',
            bio: 'Dr. Parker helps couples and families improve communication and resolve conflicts through evidence-based therapeutic approaches.'
        },
        'Dr. James Rodriguez': {
            specialization: 'Addiction Specialist',
            experience: '18+ years',
            education: 'Ph.D. in Clinical Psychology, Stanford University',
            expertise: ['Substance Abuse', 'Addiction Recovery', 'Dual Diagnosis', 'Group Therapy', 'Relapse Prevention'],
            languages: ['English', 'Spanish', 'Portuguese'],
            rating: 4.7,
            reviews: 120,
            availability: 'Mon-Fri: 8 AM - 5 PM',
            bio: 'Dr. Rodriguez specializes in addiction treatment and recovery, with expertise in both individual and group therapy settings.'
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
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title fw-bold">
                            <i class="fas fa-user-md me-2"></i>${doctorName}
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-4 text-center border-end">
                                <div class="doctor-profile-image mb-3">
                                    <div style="width: 150px; height: 150px; margin: 0 auto; border-radius: 50%; background: linear-gradient(135deg, #7c9cbf, #9d9cb3); display: flex; align-items: center; justify-content: center; font-size: 3rem; color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                                        ${doctorName.split(' ').map(n => n[0]).join('')}
                                    </div>
                                </div>
                                <h6 class="fw-bold text-primary">${profile.specialization}</h6>
                                <div class="mb-3">
                                    <i class="fas fa-star" style="color: #ffb74d;"></i> ${profile.rating} 
                                    <span class="text-muted small">(${profile.reviews} reviews)</span>
                                </div>
                                <div class="mb-2">
                                    <i class="fas fa-briefcase text-primary me-2"></i>
                                    <span class="small">${profile.experience}</span>
                                </div>
                                <div class="mb-2">
                                    <i class="fas fa-clock text-success me-2"></i>
                                    <span class="small">${profile.availability}</span>
                                </div>
                            </div>
                            <div class="col-md-8">
                                <h6 class="fw-bold mb-3"><i class="fas fa-info-circle me-2"></i>About</h6>
                                <p class="text-muted">${profile.bio}</p>
                                
                                <h6 class="fw-bold mb-2 mt-3"><i class="fas fa-graduation-cap me-2"></i>Education</h6>
                                <p class="small">${profile.education}</p>
                                
                                <h6 class="fw-bold mb-2 mt-3"><i class="fas fa-stethoscope me-2"></i>Areas of Expertise</h6>
                                <div class="d-flex flex-wrap gap-2 mb-3">
                                    ${profile.expertise.map(exp => `
                                        <span class="badge" style="background: rgba(124, 156, 191, 0.2); color: #7c9cbf; padding: 0.5rem 1rem; font-weight: 500; border-radius: 20px;">
                                            ${exp}
                                        </span>
                                    `).join('')}
                                </div>
                                
                                <h6 class="fw-bold mb-2 mt-3"><i class="fas fa-language me-2"></i>Languages</h6>
                                <p class="small">${profile.languages.join(', ')}</p>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-success" onclick="scheduleAppointment('${doctorName}'); bootstrap.Modal.getInstance(document.getElementById('profileModal')).hide();">
                            <i class="fas fa-calendar me-2"></i>Schedule Appointment
                        </button>
                        <button type="button" class="btn btn-primary" onclick="startVideoCall('${doctorName}'); bootstrap.Modal.getInstance(document.getElementById('profileModal')).hide();">
                            <i class="fas fa-video me-2"></i>Start Video Call
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal
    const existingModal = document.getElementById('profileModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    const modal = new bootstrap.Modal(document.getElementById('profileModal'));
    modal.show();
}

function scheduleAppointment(doctorName) {
    const modalHTML = `
        <div class="modal fade" id="scheduleModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title fw-bold">
                            <i class="fas fa-calendar-check me-2"></i>Schedule Appointment
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="appointmentForm">
                            <div class="mb-3">
                                <label class="form-label fw-bold">Doctor</label>
                                <input type="text" class="form-control" value="${doctorName}" readonly>
                            </div>
                            <div class="mb-3">
                                <label class="form-label fw-bold">Your Name</label>
                                <input type="text" class="form-control" id="patientName" placeholder="Enter your name" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label fw-bold">Email</label>
                                <input type="email" class="form-control" id="patientEmail" placeholder="your@email.com" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label fw-bold">Appointment Date</label>
                                <input type="date" class="form-control" id="appointmentDate" required min="${new Date().toISOString().split('T')[0]}">
                            </div>
                            <div class="mb-3">
                                <label class="form-label fw-bold">Preferred Time</label>
                                <select class="form-select" id="appointmentTime" required>
                                    <option value="">Select time...</option>
                                    <option value="09:00">9:00 AM</option>
                                    <option value="10:00">10:00 AM</option>
                                    <option value="11:00">11:00 AM</option>
                                    <option value="12:00">12:00 PM</option>
                                    <option value="14:00">2:00 PM</option>
                                    <option value="15:00">3:00 PM</option>
                                    <option value="16:00">4:00 PM</option>
                                    <option value="17:00">5:00 PM</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label fw-bold">Reason for Consultation (Optional)</label>
                                <textarea class="form-control" id="appointmentReason" rows="3" placeholder="Briefly describe what you'd like to discuss..."></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="submitAppointment('${doctorName}')">
                            <i class="fas fa-calendar-check me-2"></i>Schedule Appointment
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const existingModal = document.getElementById('scheduleModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    const modal = new bootstrap.Modal(document.getElementById('scheduleModal'));
    modal.show();
}

function submitAppointment(doctorName) {
    const patientName = document.getElementById('patientName').value;
    const patientEmail = document.getElementById('patientEmail').value;
    const date = document.getElementById('appointmentDate').value;
    const time = document.getElementById('appointmentTime').value;
    const reason = document.getElementById('appointmentReason').value;
    
    if (!patientName || !patientEmail || !date || !time) {
        showNotification('Please fill in all required fields', 'warning');
        return;
    }
    
    const appointmentData = {
        doctor: doctorName,
        patient_name: patientName,
        patient_email: patientEmail,
        date: date,
        time: time,
        reason: reason
    };
    
    console.log('Appointment scheduled:', appointmentData);
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('scheduleModal'));
    modal.hide();
    
    showNotification(`Appointment scheduled with ${doctorName} on ${date} at ${time}. Confirmation email sent to ${patientEmail}`, 'success');
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} position-fixed top-0 start-50 translate-middle-x mt-3`;
    notification.style.zIndex = '10000';
    notification.style.minWidth = '300px';
    notification.style.maxWidth = '500px';
    notification.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>${message}`;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Cleanup on modal close
document.addEventListener('DOMContentLoaded', () => {
    console.log('Doctor page loaded');
    
    // Check if Jitsi API script is loaded
    if (typeof JitsiMeetExternalAPI === 'undefined') {
        console.warn('⚠️ Jitsi Meet API not loaded yet');
    } else {
        console.log('✅ Jitsi Meet API is ready');
    }
    
    const videoModal = document.getElementById('videoCallModal');
    
    if (videoModal) {
        videoModal.addEventListener('hidden.bs.modal', () => {
            console.log('Video modal closed');
            
            // Cleanup Jitsi
            if (jitsiApi) {
                try {
                    jitsiApi.dispose();
                    console.log('Jitsi API disposed');
                } catch (e) {
                    console.log('Error disposing Jitsi:', e);
                }
                jitsiApi = null;
            }
            
            // Clear container
            const container = document.getElementById('jitsiContainer');
            if (container) {
                container.innerHTML = '';
            }
            
            console.log('Video call cleanup complete');
        });
    }
});