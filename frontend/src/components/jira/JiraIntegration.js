import React, { useState, useEffect } from 'react';
import axios from 'axios';
import config from '../../config';
import './JiraIntegration.css';

const JiraIntegration = ({ testId, testType, testName, testResult, errorMessage }) => {
  const [jiraIssues, setJiraIssues] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Jira 이슈 조회
  const fetchJiraIssues = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${config.apiUrl}/jira/integrations`, {
        params: {
          test_id: testId,
          test_type: testType
        }
      });
      
      if (response.data.success) {
        setJiraIssues(response.data.data);
      }
    } catch (err) {
      console.error('Jira 이슈 조회 오류:', err);
      setError('Jira 이슈를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // Jira 이슈 생성
  const createJiraIssue = async (issueData) => {
    try {
      setLoading(true);
      const response = await axios.post(`${config.apiUrl}/jira/issues`, {
        test_id: testId,
        test_type: testType,
        ...issueData
      });
      
      if (response.data.success) {
        setShowCreateModal(false);
        fetchJiraIssues();
        alert('Jira 이슈가 성공적으로 생성되었습니다.');
      }
    } catch (err) {
      console.error('Jira 이슈 생성 오류:', err);
      alert('Jira 이슈 생성 중 오류가 발생했습니다: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 자동 이슈 생성 (테스트 실패 시)
  const autoCreateIssue = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${config.apiUrl}/jira/auto-create`, {
        test_id: testId,
        test_type: testType,
        test_name: testName,
        test_result: testResult,
        error_message: errorMessage
      });
      
      if (response.data.success) {
        if (response.data.data) {
          fetchJiraIssues();
          alert('테스트 실패로 인해 Jira 이슈가 자동 생성되었습니다.');
        } else {
          alert('테스트가 성공했으므로 이슈를 생성하지 않습니다.');
        }
      }
    } catch (err) {
      console.error('자동 이슈 생성 오류:', err);
      alert('자동 이슈 생성 중 오류가 발생했습니다: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  // Jira 이슈 상태 업데이트
  const updateIssueStatus = async (issueKey, newStatus) => {
    try {
      const response = await axios.put(`${config.apiUrl}/jira/issues/${issueKey}`, {
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

  // Jira 이슈에 댓글 추가
  const addComment = async (issueKey, comment) => {
    try {
      const response = await axios.post(`${config.apiUrl}/jira/issues/${issueKey}/comment`, {
        comment: comment
      });
      
      if (response.data.success) {
        alert('댓글이 추가되었습니다.');
      }
    } catch (err) {
      console.error('댓글 추가 오류:', err);
      alert('댓글 추가 중 오류가 발생했습니다: ' + (err.response?.data?.error || err.message));
    }
  };

  useEffect(() => {
    if (testId && testType) {
      fetchJiraIssues();
    }
  }, [testId, testType]);

  return (
    <div className="jira-integration">
      <div className="jira-header">
        <h3>🔗 Jira 연동</h3>
        <div className="jira-actions">
          <button 
            className="btn btn-primary"
            onClick={() => setShowCreateModal(true)}
            disabled={loading}
          >
            ➕ Jira 이슈 생성
          </button>
          {testResult && ['Fail', 'Error'].includes(testResult) && (
            <button 
              className="btn btn-warning"
              onClick={autoCreateIssue}
              disabled={loading}
            >
              🤖 자동 이슈 생성
            </button>
          )}
        </div>
      </div>
      
      {loading && (
        <div className="loading">로딩 중...</div>
      )}
      
      {error && (
        <div className="error">{error}</div>
      )}
      
      {/* Jira 이슈 목록 */}
      <div className="jira-issues">
        {jiraIssues.length === 0 ? (
          <div className="no-issues">
            <p>연동된 Jira 이슈가 없습니다.</p>
          </div>
        ) : (
          jiraIssues.map(issue => (
            <div key={issue.id} className="jira-issue">
              <div className="issue-info">
                <div className="issue-header">
                  <span className="issue-key">{issue.jira_issue_key}</span>
                  <span className={`issue-status status-${issue.status.toLowerCase().replace(' ', '-')}`}>
                    {issue.status}
                  </span>
                </div>
                <div className="issue-summary">{issue.summary}</div>
                <div className="issue-meta">
                  <span className="issue-type">{issue.issue_type}</span>
                  <span className="issue-priority">{issue.priority}</span>
                  <span className="issue-created">
                    {new Date(issue.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              
              <div className="issue-actions">
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
                    const comment = prompt('댓글을 입력하세요:');
                    if (comment) {
                      addComment(issue.jira_issue_key, comment);
                    }
                  }}
                >
                  💬 댓글
                </button>
                
                <button 
                  className="btn btn-info btn-sm"
                  onClick={() => window.open(`https://mock-jira.atlassian.net/browse/${issue.jira_issue_key}`, '_blank')}
                >
                  🔗 Jira에서 보기
                </button>
              </div>
            </div>
          ))
        )}
      </div>
      
      {/* 이슈 생성 모달 */}
      {showCreateModal && (
        <JiraIssueModal 
          onSubmit={createJiraIssue}
          onClose={() => setShowCreateModal(false)}
          testName={testName}
          testResult={testResult}
          errorMessage={errorMessage}
        />
      )}
    </div>
  );
};

// Jira 이슈 생성 모달 컴포넌트
const JiraIssueModal = ({ onSubmit, onClose, testName, testResult, errorMessage }) => {
  const [issueData, setIssueData] = useState({
    summary: testName ? `테스트 실패: ${testName}` : '',
    description: testResult && errorMessage ? 
      `**테스트 정보**\n- 테스트명: ${testName}\n- 결과: ${testResult}\n\n**오류 정보**\n${errorMessage}` : '',
    issue_type: 'Bug',
    priority: 'Medium'
  });
  const [isClosing, setIsClosing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 모달이 열릴 때 배경 스크롤 방지
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    
    // ESC 키로 모달 닫기
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        handleClose();
      }
    };
    
    document.addEventListener('keydown', handleEscape);
    
    return () => {
      document.body.style.overflow = 'unset';
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!issueData.summary.trim()) {
      alert('이슈 요약을 입력해주세요.');
      return;
    }
    if (issueData.summary.length < 5) {
      alert('이슈 요약은 5자 이상 입력해주세요.');
      return;
    }
    
    setIsSubmitting(true);
    try {
      await onSubmit(issueData);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      onClose();
    }, 200);
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      handleClose();
    }
  };

  return (
    <div className={`jira-modal-overlay ${isClosing ? 'closing' : ''}`} onClick={handleOverlayClick}>
      <div className={`jira-modal ${isClosing ? 'closing' : ''}`}>
        <div className="jira-modal-header">
          <div className="jira-modal-title">
            <span className="jira-modal-icon">🔗</span>
            <h3>Jira 이슈 생성</h3>
          </div>
          <button className="jira-modal-close" onClick={handleClose} title="닫기">×</button>
        </div>
        
        <form onSubmit={handleSubmit} className="jira-modal-body">
          <div className="form-group">
            <label>이슈 요약 *</label>
            <input
              type="text"
              className={`form-control ${issueData.summary.length > 0 && issueData.summary.length < 5 ? 'error' : ''}`}
              value={issueData.summary}
              onChange={(e) => setIssueData({...issueData, summary: e.target.value})}
              placeholder="이슈 요약을 입력하세요 (5자 이상)"
              required
            />
            {issueData.summary.length > 0 && issueData.summary.length < 5 && (
              <div className="form-error">이슈 요약은 5자 이상 입력해주세요.</div>
            )}
          </div>
          
          <div className="form-group">
            <label>설명</label>
            <textarea
              className="form-control"
              value={issueData.description}
              onChange={(e) => setIssueData({...issueData, description: e.target.value})}
              placeholder="이슈 상세 설명을 입력하세요"
              rows="5"
            />
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label>이슈 타입</label>
              <select
                className="form-control"
                value={issueData.issue_type}
                onChange={(e) => setIssueData({...issueData, issue_type: e.target.value})}
              >
                <option value="Bug">🐛 Bug</option>
                <option value="Task">📋 Task</option>
                <option value="Story">📖 Story</option>
                <option value="Epic">🏗️ Epic</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>우선순위</label>
              <select
                className="form-control"
                value={issueData.priority}
                onChange={(e) => setIssueData({...issueData, priority: e.target.value})}
              >
                <option value="Low">🟢 Low</option>
                <option value="Medium">🟡 Medium</option>
                <option value="High">🟠 High</option>
                <option value="Critical">🔴 Critical</option>
              </select>
            </div>
          </div>
        </form>
        
        <div className="jira-modal-actions">
          <button className="btn btn-secondary" onClick={handleClose}>
            취소
          </button>
          <button 
            className="btn btn-primary" 
            onClick={handleSubmit}
            disabled={!issueData.summary.trim() || isSubmitting}
          >
            {isSubmitting ? '생성 중...' : '생성'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default JiraIntegration;
