import React, { useState, useEffect } from 'react';
import axios from 'axios';
import config from '../../config';
import './JiraIssuesList.css';

const JiraIssuesList = () => {
  const [jiraIssues, setJiraIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [issueTypeFilter, setIssueTypeFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(20);
  const [totalItems, setTotalItems] = useState(0);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showAssigneeModal, setShowAssigneeModal] = useState(false);
  const [showLabelModal, setShowLabelModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [assigneeEmail, setAssigneeEmail] = useState('');
  const [newLabel, setNewLabel] = useState('');
  const [testCases, setTestCases] = useState([]);
  const [editFormData, setEditFormData] = useState({
    summary: '',
    description: '',
    status: '',
    priority: '',
    issue_type: ''
  });
  const [comments, setComments] = useState([]);
  const [showComments, setShowComments] = useState(false);
  const [loadingComments, setLoadingComments] = useState(false);

  // 테스트 케이스 목록 조회
  const fetchTestCases = async () => {
    try {
      const response = await axios.get(`${config.apiUrl}/testcases`);
      if (response.data.success) {
        setTestCases(response.data.data);
      }
    } catch (err) {
      console.error('테스트 케이스 조회 오류:', err);
    }
  };

  // JIRA 이슈 목록 조회
  const fetchJiraIssues = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get(`${config.apiUrl}/api/jira/integrations`);
      
      if (response.data.success) {
        setJiraIssues(response.data.data);
        setTotalItems(response.data.data.length);
      }
    } catch (err) {
      console.error('JIRA 이슈 조회 오류:', err);
      setError('JIRA 이슈를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 이슈 상태 업데이트
  const updateIssueStatus = async (issueKey, newStatus) => {
    try {
      const response = await axios.put(`${config.apiUrl}/api/jira/issues/${issueKey}`, {
        status: newStatus
      });
      
      if (response.data.success) {
        fetchJiraIssues();
        alert('이슈 상태가 업데이트되었습니다.');
      }
    } catch (err) {
      console.error('이슈 상태 업데이트 오류:', err);
      alert('이슈 상태 업데이트 중 오류가 발생했습니다: ' + (err.response?.data?.error || err.message));
    }
  };

  // 이슈에 댓글 추가
  const addComment = async (issueKey, comment) => {
    try {
      const response = await axios.post(`${config.apiUrl}/api/jira/issues/${issueKey}/comment`, {
        comment: comment
      });
      
      if (response.data.success) {
        alert('댓글이 추가되었습니다.');
        // 댓글 목록 새로고침
        fetchComments(issueKey);
      }
    } catch (err) {
      console.error('댓글 추가 오류:', err);
      
      // 404 오류인 경우 특별한 메시지 표시
      if (err.response?.status === 404 && err.response?.data?.error_type === 'ISSUE_NOT_FOUND') {
        alert('이슈가 존재하지 않습니다.\nMock 서버가 재시작되어 이슈가 삭제되었을 수 있습니다.\n새 이슈를 생성한 후 다시 시도해주세요.');
      } else {
        alert('댓글 추가 중 오류가 발생했습니다: ' + (err.response?.data?.error || err.message));
      }
    }
  };

  // 담당자 할당
  const assignIssue = async (issueKey, assigneeEmail) => {
    try {
      const response = await axios.put(`${config.apiUrl}/api/jira/issues/${issueKey}`, {
        assignee: assigneeEmail
      });
      
      if (response.data.success) {
        fetchJiraIssues();
        alert('담당자가 할당되었습니다.');
        setShowAssigneeModal(false);
        setAssigneeEmail('');
      }
    } catch (err) {
      console.error('담당자 할당 오류:', err);
      alert('담당자 할당 중 오류가 발생했습니다: ' + (err.response?.data?.error || err.message));
    }
  };

  // 레이블 추가
  const addLabel = async (issueKey, label) => {
    try {
      const response = await axios.put(`${config.apiUrl}/api/jira/issues/${issueKey}`, {
        labels: [label]
      });
      
      if (response.data.success) {
        fetchJiraIssues();
        alert('레이블이 추가되었습니다.');
        setShowLabelModal(false);
        setNewLabel('');
      }
    } catch (err) {
      console.error('레이블 추가 오류:', err);
      alert('레이블 추가 중 오류가 발생했습니다: ' + (err.response?.data?.error || err.message));
    }
  };

  // 댓글 조회
  const fetchComments = async (issueKey) => {
    setLoadingComments(true);
    try {
      const response = await axios.get(`${config.apiUrl}/api/jira/issues/${issueKey}/comments`);
      if (response.data.success) {
        setComments(response.data.data.comments || []);
      }
    } catch (err) {
      console.error('댓글 조회 오류:', err);
      setComments([]);
    } finally {
      setLoadingComments(false);
    }
  };

  // 이슈 상세보기
  const showIssueDetail = (issue) => {
    setSelectedIssue(issue);
    setShowDetailModal(true);
    fetchComments(issue.jira_issue_key);
  };

  // 이슈 수정 모달 열기
  const openEditModal = (issue) => {
    setSelectedIssue(issue);
    setEditFormData({
      summary: issue.summary || '',
      description: issue.description || '',
      status: issue.status || 'To Do',
      priority: issue.priority || 'Medium',
      issue_type: issue.issue_type || 'Task'
    });
    setShowEditModal(true);
  };

  // 이슈 수정
  const updateIssue = async () => {
    if (!selectedIssue) return;

    try {
      const response = await axios.put(`${config.apiUrl}/api/jira/issues/${selectedIssue.jira_issue_key}`, {
        summary: editFormData.summary,
        description: editFormData.description,
        status: editFormData.status,
        priority: editFormData.priority,
        issue_type: editFormData.issue_type
      });
      
      if (response.data.success) {
        fetchJiraIssues();
        alert('이슈가 성공적으로 수정되었습니다.');
        setShowEditModal(false);
        setShowDetailModal(false);
      }
    } catch (err) {
      console.error('이슈 수정 오류:', err);
      alert('이슈 수정 중 오류가 발생했습니다: ' + (err.response?.data?.error || err.message));
    }
  };

  // 필터링된 이슈 목록
  const getFilteredIssues = () => {
    return jiraIssues.filter(issue => {
      const matchesSearch = !searchTerm || 
        issue.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
        issue.jira_issue_key.toLowerCase().includes(searchTerm.toLowerCase()) ||
        issue.description.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = statusFilter === 'all' || issue.status === statusFilter;
      const matchesPriority = priorityFilter === 'all' || issue.priority === priorityFilter;
      const matchesType = issueTypeFilter === 'all' || issue.issue_type === issueTypeFilter;
      
      return matchesSearch && matchesStatus && matchesPriority && matchesType;
    });
  };

  // 페이지네이션
  const getPaginatedIssues = () => {
    const filtered = getFilteredIssues();
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filtered.slice(startIndex, endIndex);
  };

  const totalPages = Math.ceil(getFilteredIssues().length / itemsPerPage);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleItemsPerPageChange = (newItemsPerPage) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1);
  };

  useEffect(() => {
    fetchJiraIssues();
    fetchTestCases();
  }, []);

  if (loading) {
    return (
      <div className="jira-issues-loading">
        <div className="loading-spinner"></div>
        <p>JIRA 이슈를 불러오는 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="jira-issues-error">
        <div className="error-icon">❌</div>
        <p>{error}</p>
        <button onClick={fetchJiraIssues} className="retry-button">
          다시 시도
        </button>
      </div>
    );
  }

  const filteredIssues = getFilteredIssues();
  const paginatedIssues = getPaginatedIssues();

  return (
    <div className="jira-issues-list-container">
      <div className="jira-issues-header">
        <h1>🔗 JIRA 이슈 관리</h1>
        <div className="header-actions">
          <button 
            className="btn btn-primary"
            onClick={fetchJiraIssues}
            disabled={loading}
          >
            🔄 새로고침
          </button>
        </div>
      </div>

      {/* 검색 및 필터 */}
      <div className="jira-issues-filters">
        <div className="search-container">
          <input
            type="text"
            placeholder="🔍 이슈 검색 (제목, 키, 설명)"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
        
        <div className="filter-container">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">모든 상태</option>
            <option value="To Do">To Do</option>
            <option value="In Progress">In Progress</option>
            <option value="Done">Done</option>
          </select>
          
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">모든 우선순위</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
            <option value="Critical">Critical</option>
          </select>
          
          <select
            value={issueTypeFilter}
            onChange={(e) => setIssueTypeFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">모든 타입</option>
            <option value="Bug">Bug</option>
            <option value="Task">Task</option>
            <option value="Story">Story</option>
            <option value="Epic">Epic</option>
          </select>
        </div>
      </div>

      {/* 페이지 크기 선택 */}
      <div className="pagination-controls-top">
        <div className="items-per-page-selector">
          <label>페이지당 항목:</label>
          <select
            value={itemsPerPage}
            onChange={(e) => handleItemsPerPageChange(Number(e.target.value))}
            className="items-per-page-select"
          >
            <option value={10}>10개</option>
            <option value={20}>20개</option>
            <option value={50}>50개</option>
            <option value={100}>100개</option>
          </select>
        </div>
        <div className="pagination-info-top">
          총 {filteredIssues.length}개 이슈 중 {Math.min((currentPage - 1) * itemsPerPage + 1, filteredIssues.length)}-{Math.min(currentPage * itemsPerPage, filteredIssues.length)}개 표시
        </div>
      </div>

      {/* 이슈 목록 */}
      <div className="jira-issues-list">
        {paginatedIssues.length === 0 ? (
          <div className="no-issues">
            <div className="no-issues-icon">📝</div>
            <p>표시할 JIRA 이슈가 없습니다.</p>
            <p>필터 조건을 조정해보세요.</p>
          </div>
        ) : (
          paginatedIssues.map(issue => (
            <div key={issue.id} className="jira-issue-card">
              <div className="issue-header">
                <div className="issue-key-section">
                  <span className="issue-key">{issue.jira_issue_key}</span>
                  <span className={`issue-status status-${issue.status.toLowerCase().replace(' ', '-')}`}>
                    {issue.status}
                  </span>
                </div>
                <div className="issue-meta">
                  <span className={`issue-type type-${issue.issue_type.toLowerCase()}`}>
                    {issue.issue_type}
                  </span>
                  <span className={`issue-priority priority-${issue.priority.toLowerCase()}`}>
                    {issue.priority}
                  </span>
                </div>
              </div>
              
              <div className="issue-content">
                <h3 className="issue-summary">{issue.summary}</h3>
                {issue.description && (
                  <p className="issue-description">{issue.description}</p>
                )}
                
                {/* 연결된 테스트 케이스 정보 */}
                {issue.test_case_id && (
                  <div className="linked-test-case">
                    <span className="linked-label">연결된 테스트:</span>
                    <span className="test-case-link">
                      {testCases.find(tc => tc.id === issue.test_case_id)?.name || `테스트 케이스 #${issue.test_case_id}`}
                    </span>
                  </div>
                )}
                
                {/* 레이블 표시 */}
                {issue.labels && (
                  <div className="issue-labels">
                    {JSON.parse(issue.labels).map((label, index) => (
                      <span key={index} className="label-tag">
                        {label}
                      </span>
                    ))}
                  </div>
                )}
                
                {/* 담당자 표시 */}
                {issue.assignee_account_id && (
                  <div className="issue-assignee">
                    <span className="assignee-label">담당자:</span>
                    <span className="assignee-name">{issue.assignee_account_id}</span>
                  </div>
                )}
              </div>
              
              <div className="issue-footer">
                <div className="issue-info">
                  <span className="issue-created">
                    생성: {new Date(issue.created_at).toLocaleDateString()}
                  </span>
                  {issue.updated_at && (
                    <span className="issue-updated">
                      수정: {new Date(issue.updated_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
                
                <div className="issue-actions">
                  <button 
                    className="btn btn-primary btn-sm"
                    onClick={() => showIssueDetail(issue)}
                    title="상세보기"
                  >
                    👁️ 상세보기
                  </button>
                  
                  <select
                    className="status-select"
                    value={issue.status}
                    onChange={(e) => updateIssueStatus(issue.jira_issue_key, e.target.value)}
                  >
                    <option value="To Do">To Do</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Done">Done</option>
                  </select>
                  
                  <button 
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      setSelectedIssue(issue);
                      setShowAssigneeModal(true);
                    }}
                    title="담당자 할당"
                  >
                    👤 담당자
                  </button>
                  
                  <button 
                    className="btn btn-warning btn-sm"
                    onClick={() => {
                      setSelectedIssue(issue);
                      setShowLabelModal(true);
                    }}
                    title="레이블 추가"
                  >
                    🏷️ 레이블
                  </button>
                  
                  <button 
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      const comment = prompt('댓글을 입력하세요:');
                      if (comment) {
                        addComment(issue.jira_issue_key, comment);
                      }
                    }}
                    title="댓글 추가"
                  >
                    💬 댓글
                  </button>
                  
                  <button 
                    className="btn btn-info btn-sm"
                    onClick={() => window.open(`https://mock-jira.atlassian.net/browse/${issue.jira_issue_key}`, '_blank')}
                    title="JIRA에서 보기"
                  >
                    🔗 Jira에서 보기
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="pagination-controls">
          <div className="pagination-buttons">
            <button
              className="pagination-btn"
              onClick={() => handlePageChange(1)}
              disabled={currentPage === 1}
            >
              &lt;&lt;
            </button>
            <button
              className="pagination-btn"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              &lt;
            </button>
            
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <button
                key={page}
                className={`pagination-btn ${currentPage === page ? 'active' : ''}`}
                onClick={() => handlePageChange(page)}
              >
                {page}
              </button>
            ))}
            
            <button
              className="pagination-btn"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              &gt;
            </button>
            <button
              className="pagination-btn"
              onClick={() => handlePageChange(totalPages)}
              disabled={currentPage === totalPages}
            >
              &gt;&gt;
            </button>
          </div>
        </div>
      )}

      {/* 이슈 상세보기 모달 */}
      {showDetailModal && selectedIssue && (
        <div className="jira-modal-overlay" onClick={() => setShowDetailModal(false)}>
          <div className="jira-modal" onClick={(e) => e.stopPropagation()}>
            <div className="jira-modal-header">
              <div className="jira-modal-title">
                <span className="jira-modal-icon">🔍</span>
                <h3>이슈 상세보기</h3>
              </div>
              <button className="jira-modal-close" onClick={() => setShowDetailModal(false)}>×</button>
            </div>
            
            <div className="jira-modal-body">
              <div className="issue-detail-content">
                <div className="detail-section">
                  <h4>기본 정보</h4>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>이슈 키:</label>
                      <span className="issue-key">{selectedIssue.jira_issue_key}</span>
                    </div>
                    <div className="detail-item">
                      <label>상태:</label>
                      <span className={`issue-status status-${selectedIssue.status.toLowerCase().replace(' ', '-')}`}>
                        {selectedIssue.status}
                      </span>
                    </div>
                    <div className="detail-item">
                      <label>타입:</label>
                      <span className={`issue-type type-${selectedIssue.issue_type.toLowerCase()}`}>
                        {selectedIssue.issue_type}
                      </span>
                    </div>
                    <div className="detail-item">
                      <label>우선순위:</label>
                      <span className={`issue-priority priority-${selectedIssue.priority.toLowerCase()}`}>
                        {selectedIssue.priority}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="detail-section">
                  <h4>제목</h4>
                  <p className="issue-summary">{selectedIssue.summary}</p>
                </div>
                
                <div className="detail-section">
                  <h4>설명</h4>
                  <div className="issue-description-full">
                    {selectedIssue.description || '설명이 없습니다.'}
                  </div>
                </div>
                
                {selectedIssue.test_case_id && (
                  <div className="detail-section">
                    <h4>연결된 테스트 케이스</h4>
                    <div className="linked-test-case-detail">
                      <span className="test-case-link">
                        {testCases.find(tc => tc.id === selectedIssue.test_case_id)?.name || `테스트 케이스 #${selectedIssue.test_case_id}`}
                      </span>
                    </div>
                  </div>
                )}
                
                {selectedIssue.labels && (
                  <div className="detail-section">
                    <h4>레이블</h4>
                    <div className="issue-labels">
                      {JSON.parse(selectedIssue.labels).map((label, index) => (
                        <span key={index} className="label-tag">
                          {label}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {selectedIssue.assignee_account_id && (
                  <div className="detail-section">
                    <h4>담당자</h4>
                    <div className="assignee-detail">
                      <span className="assignee-name">{selectedIssue.assignee_account_id}</span>
                    </div>
                  </div>
                )}
                
                <div className="detail-section">
                  <h4>생성 정보</h4>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>생성일:</label>
                      <span>{new Date(selectedIssue.created_at).toLocaleString()}</span>
                    </div>
                    <div className="detail-item">
                      <label>수정일:</label>
                      <span>{selectedIssue.updated_at ? new Date(selectedIssue.updated_at).toLocaleString() : '없음'}</span>
                    </div>
                    <div className="detail-item">
                      <label>마지막 동기화:</label>
                      <span>{selectedIssue.last_sync_at ? new Date(selectedIssue.last_sync_at).toLocaleString() : '없음'}</span>
                    </div>
                  </div>
                </div>
                
                <div className="detail-section">
                  <div className="comments-header">
                    <h4>댓글 ({comments.length})</h4>
                    <button 
                      className="btn btn-sm btn-outline"
                      onClick={() => setShowComments(!showComments)}
                    >
                      {showComments ? '숨기기' : '보기'}
                    </button>
                  </div>
                  
                  {showComments && (
                    <div className="comments-list">
                      {loadingComments ? (
                        <div className="comments-loading">
                          <div className="loading-spinner"></div>
                          <span>댓글을 불러오는 중...</span>
                        </div>
                      ) : comments.length === 0 ? (
                        <div className="no-comments">
                          <div className="no-comments-icon">💬</div>
                          <p>댓글이 없습니다.</p>
                          <small>첫 번째 댓글을 작성해보세요!</small>
                        </div>
                      ) : (
                        comments.map((comment, index) => (
                          <div key={index} className="comment-item">
                            <div className="comment-header">
                              <span className="comment-author">
                                {comment.author?.displayName || 'Unknown User'}
                              </span>
                              <span className="comment-date">
                                {new Date(comment.created).toLocaleString('ko-KR')}
                              </span>
                            </div>
                            <div className="comment-body">
                              {comment.body}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            <div className="jira-modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowDetailModal(false)}>
                닫기
              </button>
              <button className="btn btn-primary" onClick={() => openEditModal(selectedIssue)}>
                ✏️ 수정
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 담당자 할당 모달 */}
      {showAssigneeModal && selectedIssue && (
        <div className="jira-modal-overlay" onClick={() => setShowAssigneeModal(false)}>
          <div className="jira-modal" onClick={(e) => e.stopPropagation()}>
            <div className="jira-modal-header">
              <div className="jira-modal-title">
                <span className="jira-modal-icon">👤</span>
                <h3>담당자 할당</h3>
              </div>
              <button className="jira-modal-close" onClick={() => setShowAssigneeModal(false)}>×</button>
            </div>
            
            <div className="jira-modal-body">
              <div className="form-group">
                <label>이슈: {selectedIssue.jira_issue_key}</label>
                <p className="issue-summary-small">{selectedIssue.summary}</p>
              </div>
              
              <div className="form-group">
                <label>담당자 이메일 *</label>
                <input
                  type="email"
                  className="form-control"
                  value={assigneeEmail}
                  onChange={(e) => setAssigneeEmail(e.target.value)}
                  placeholder="담당자 이메일을 입력하세요"
                  required
                />
              </div>
            </div>
            
            <div className="jira-modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowAssigneeModal(false)}>
                취소
              </button>
              <button 
                className="btn btn-primary" 
                onClick={() => assignIssue(selectedIssue.jira_issue_key, assigneeEmail)}
                disabled={!assigneeEmail.trim()}
              >
                할당
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 레이블 추가 모달 */}
      {showLabelModal && selectedIssue && (
        <div className="jira-modal-overlay" onClick={() => setShowLabelModal(false)}>
          <div className="jira-modal" onClick={(e) => e.stopPropagation()}>
            <div className="jira-modal-header">
              <div className="jira-modal-title">
                <span className="jira-modal-icon">🏷️</span>
                <h3>레이블 추가</h3>
              </div>
              <button className="jira-modal-close" onClick={() => setShowLabelModal(false)}>×</button>
            </div>
            
            <div className="jira-modal-body">
              <div className="form-group">
                <label>이슈: {selectedIssue.jira_issue_key}</label>
                <p className="issue-summary-small">{selectedIssue.summary}</p>
              </div>
              
              <div className="form-group">
                <label>레이블 *</label>
                <input
                  type="text"
                  className="form-control"
                  value={newLabel}
                  onChange={(e) => setNewLabel(e.target.value)}
                  placeholder="레이블을 입력하세요"
                  required
                />
                <small className="form-help">여러 레이블을 추가하려면 쉼표로 구분하세요</small>
              </div>
            </div>
            
            <div className="jira-modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowLabelModal(false)}>
                취소
              </button>
              <button 
                className="btn btn-primary" 
                onClick={() => addLabel(selectedIssue.jira_issue_key, newLabel)}
                disabled={!newLabel.trim()}
              >
                추가
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 이슈 수정 모달 */}
      {showEditModal && selectedIssue && (
        <div className="jira-modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="jira-modal" onClick={(e) => e.stopPropagation()}>
            <div className="jira-modal-header">
              <div className="jira-modal-title">
                <span className="jira-modal-icon">✏️</span>
                <h3>이슈 수정</h3>
              </div>
              <button className="jira-modal-close" onClick={() => setShowEditModal(false)}>×</button>
            </div>
            
            <div className="jira-modal-body">
              <div className="form-group">
                <label>이슈 키: {selectedIssue.jira_issue_key}</label>
              </div>
              
              <div className="form-group">
                <label>제목 *</label>
                <input
                  type="text"
                  className="form-control"
                  value={editFormData.summary}
                  onChange={(e) => setEditFormData({...editFormData, summary: e.target.value})}
                  placeholder="이슈 제목을 입력하세요"
                  required
                />
              </div>
              
              <div className="form-group">
                <label>설명</label>
                <textarea
                  className="form-control"
                  value={editFormData.description}
                  onChange={(e) => setEditFormData({...editFormData, description: e.target.value})}
                  placeholder="이슈 설명을 입력하세요"
                  rows="5"
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>상태</label>
                  <select
                    className="form-control"
                    value={editFormData.status}
                    onChange={(e) => setEditFormData({...editFormData, status: e.target.value})}
                  >
                    <option value="To Do">To Do</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Done">Done</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label>우선순위</label>
                  <select
                    className="form-control"
                    value={editFormData.priority}
                    onChange={(e) => setEditFormData({...editFormData, priority: e.target.value})}
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Critical">Critical</option>
                  </select>
                </div>
              </div>
              
              <div className="form-group">
                <label>이슈 타입</label>
                <select
                  className="form-control"
                  value={editFormData.issue_type}
                  onChange={(e) => setEditFormData({...editFormData, issue_type: e.target.value})}
                >
                  <option value="Bug">🐛 Bug</option>
                  <option value="Task">📋 Task</option>
                  <option value="Story">📖 Story</option>
                  <option value="Epic">🏗️ Epic</option>
                </select>
              </div>
            </div>
            
            <div className="jira-modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowEditModal(false)}>
                취소
              </button>
              <button 
                className="btn btn-primary" 
                onClick={updateIssue}
                disabled={!editFormData.summary.trim()}
              >
                저장
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JiraIssuesList;
