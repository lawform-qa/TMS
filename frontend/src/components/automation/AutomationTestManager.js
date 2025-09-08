import React, { useState, useEffect } from 'react';
import axios from 'axios';
import config from '../../config';
import { useAuth } from '../../contexts/AuthContext';
import AutomationTestDetail from './AutomationTestDetail';
import './AutomationTestManager.css';

axios.defaults.baseURL = config.apiUrl;

const AutomationTestManager = () => {
  const { user } = useAuth();
  const [automationTests, setAutomationTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingTest, setEditingTest] = useState(null);
  // 하단 전체 화면 구조로 변경
  const [selectedTest, setSelectedTest] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [users, setUsers] = useState([]);
  const [newTest, setNewTest] = useState({
    name: '',
    description: '',
    test_type: 'playwright',
    script_path: '',
    environment: 'dev',
    parameters: '',
    assignee_id: null
  });

  // 검색 및 필터링 관련 상태
  const [searchTerm, setSearchTerm] = useState('');
  const [testTypeFilter, setTestTypeFilter] = useState('all');
  const [environmentFilter, setEnvironmentFilter] = useState('all');
  const [assigneeFilter, setAssigneeFilter] = useState('all');
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  useEffect(() => {
    fetchAutomationTests();
  }, []);

  const fetchAutomationTests = async () => {
    try {
      setLoading(true);
      
      // 자동화 테스트 목록은 항상 가져오기
      const automationRes = await axios.get('/automation-tests');
      setAutomationTests(automationRes.data.items || automationRes.data);
      
      // 사용자 목록은 admin이나 user만 가져오기 (게스트는 제외)
      if (user && (user.role === 'admin' || user.role === 'user')) {
        try {
          const usersRes = await axios.get('/users/list');
          setUsers(usersRes.data);
        } catch (userErr) {
          console.error('사용자 목록 조회 오류:', userErr);
          setUsers([]);
        }
      } else {
        setUsers([]);
      }
    } catch (err) {
      setError('자동화 테스트 목록을 불러오는 중 오류가 발생했습니다.');
      console.error('Automation test fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTest = async () => {
    if (!newTest.name || !newTest.script_path) {
      alert('테스트명과 스크립트 경로를 입력해주세요.');
      return;
    }

    try {
      await axios.post('/automation-tests', newTest);
      alert('자동화 테스트가 성공적으로 추가되었습니다.');
      setShowAddModal(false);
      setNewTest({
        name: '',
        description: '',
        test_type: 'playwright',
        script_path: '',
        environment: 'dev',
        parameters: '',
        assignee_id: null
      });
      fetchAutomationTests();
    } catch (err) {
      alert('자동화 테스트 추가 중 오류가 발생했습니다: ' + err.response?.data?.error || err.message);
    }
  };

  const handleEditTest = async () => {
    if (!editingTest.name || !editingTest.script_path) {
      alert('테스트명과 스크립트 경로를 입력해주세요.');
      return;
    }

    try {
      await axios.put(`/automation-tests/${editingTest.id}`, editingTest);
      alert('자동화 테스트가 성공적으로 수정되었습니다.');
      setShowEditModal(false);
      setEditingTest(null);
      fetchAutomationTests();
    } catch (err) {
      alert('자동화 테스트 수정 중 오류가 발생했습니다: ' + err.response?.data?.error || err.message);
    }
  };

  const handleEditClick = (test) => {
    setEditingTest({
      ...test,
      assignee_id: test.assignee_id || null
    });
    setShowEditModal(true);
  };

  const handleDeleteTest = async (testId) => {
    if (!window.confirm('정말로 이 자동화 테스트를 삭제하시겠습니까?')) {
      return;
    }

    try {
      await axios.delete(`/automation-tests/${testId}`);
      alert('자동화 테스트가 성공적으로 삭제되었습니다.');
      fetchAutomationTests();
    } catch (err) {
      alert('자동화 테스트 삭제 중 오류가 발생했습니다: ' + err.response?.data?.error || err.message);
    }
  };

  const handleExecuteTest = async (testId) => {
    if (!window.confirm('이 자동화 테스트를 실행하시겠습니까?')) {
      return;
    }

    try {
      await axios.post(`/automation-tests/${testId}/execute`);
      alert('자동화 테스트 실행이 완료되었습니다.');
      fetchAutomationTests();
    } catch (err) {
      alert('자동화 테스트 실행 중 오류가 발생했습니다: ' + err.response?.data?.error || err.message);
    }
  };

  // 상세보기 토글 함수를 하단 전체 화면용으로 변경
  const toggleTestDetails = (test) => {
    if (selectedTest && selectedTest.id === test.id) {
      // 같은 테스트를 다시 클릭하면 닫기
      setSelectedTest(null);
      setShowDetail(false);
    } else {
      // 다른 테스트를 클릭하면 선택하고 표시
      setSelectedTest(test);
      setShowDetail(true);
    }
  };

  // 상세보기 닫기
  const closeDetail = () => {
    setSelectedTest(null);
    setShowDetail(false);
  };

  // 필터링된 자동화 테스트 목록 반환
  const getFilteredAutomationTests = () => {
    let filtered = [...automationTests];

    // 검색어 필터링
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(test => 
        (test.name && test.name.toLowerCase().includes(searchLower)) ||
        (test.description && test.description.toLowerCase().includes(searchLower)) ||
        (test.script_path && test.script_path.toLowerCase().includes(searchLower)) ||
        (test.creator_name && test.creator_name.toLowerCase().includes(searchLower)) ||
        (test.assignee_name && test.assignee_name.toLowerCase().includes(searchLower))
      );
    }

    // 테스트 타입 필터
    if (testTypeFilter !== 'all') {
      filtered = filtered.filter(test => test.test_type === testTypeFilter);
    }

    // 환경 필터
    if (environmentFilter !== 'all') {
      filtered = filtered.filter(test => test.environment === environmentFilter);
    }

    // 담당자 필터
    if (assigneeFilter !== 'all') {
      filtered = filtered.filter(test => test.assignee_name === assigneeFilter);
    }

    // 정렬
    filtered.sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];

      if (sortBy === 'created_at' || sortBy === 'updated_at') {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      } else if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  };

  // 검색 초기화
  const clearSearch = () => {
    setSearchTerm('');
    setTestTypeFilter('all');
    setEnvironmentFilter('all');
    setAssigneeFilter('all');
    setSortBy('name');
    setSortOrder('asc');
  };

  // 정렬 핸들러
  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  // 고유한 담당자 목록 생성
  const getUniqueAssignees = () => {
    const assignees = automationTests
      .map(test => test.assignee_name)
      .filter(name => name)
      .filter((name, index, arr) => arr.indexOf(name) === index);
    return assignees;
  };

  if (loading) {
    return <div className="loading">자동화 테스트 목록을 불러오는 중...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  const filteredTests = getFilteredAutomationTests();

  return (
    <div className="automation-test-manager">
      <div className="automation-header">
        <h2>자동화 테스트 관리</h2>
        <div className="header-actions">
          {user && (user.role === 'admin' || user.role === 'user') && (
            <button 
              className="btn btn-add"
              onClick={() => setShowAddModal(true)}
            >
              ➕ 자동화 테스트 추가
            </button>
          )}
        </div>
      </div>

      {/* 검색 섹션 */}
      <div className="search-section">
        <div className="search-container">
          <div className="search-input-wrapper">
            <input
              type="text"
              className="search-input"
              placeholder="자동화 테스트 검색 (이름, 설명, 스크립트 경로, 작성자, 담당자)"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <button 
                className="btn-clear-search"
                onClick={clearSearch}
                title="검색 초기화"
              >
                ✕
              </button>
            )}
          </div>
          
          <div className="search-info">
            {searchTerm || testTypeFilter !== 'all' || environmentFilter !== 'all' || assigneeFilter !== 'all' ? (
              <span>검색 결과: {filteredTests.length}개</span>
            ) : (
              <span>전체 자동화 테스트: {automationTests.length}개</span>
            )}
          </div>

          {/* 고급 필터 */}
          <div className="advanced-filters">
            <div className="filter-row">
              <div className="filter-group">
                <label>테스트 타입</label>
                <select
                  value={testTypeFilter}
                  onChange={(e) => setTestTypeFilter(e.target.value)}
                  className="filter-select"
                >
                  <option value="all">전체</option>
                  <option value="playwright">Playwright</option>
                  <option value="selenium">Selenium</option>
                  <option value="cypress">Cypress</option>
                  <option value="puppeteer">Puppeteer</option>
                </select>
              </div>
              
              <div className="filter-group">
                <label>환경</label>
                <select
                  value={environmentFilter}
                  onChange={(e) => setEnvironmentFilter(e.target.value)}
                  className="filter-select"
                >
                  <option value="all">전체</option>
                  <option value="dev">DEV</option>
                  <option value="alpha">ALPHA</option>
                  <option value="production">PRODUCTION</option>
                </select>
              </div>
              
              <div className="filter-group">
                <label>담당자</label>
                <select
                  value={assigneeFilter}
                  onChange={(e) => setAssigneeFilter(e.target.value)}
                  className="filter-select"
                >
                  <option value="all">전체</option>
                  {getUniqueAssignees().map(assignee => (
                    <option key={assignee} value={assignee}>
                      {assignee}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 테이블 형태의 테스트 목록 */}
      <div className="automation-table-container">
        {filteredTests.length === 0 ? (
          <div className="empty-state">
            <p>검색 조건에 맞는 자동화 테스트가 없습니다.</p>
            {(searchTerm || testTypeFilter !== 'all' || environmentFilter !== 'all' || assigneeFilter !== 'all') && (
              <button 
                className="btn btn-primary"
                onClick={clearSearch}
              >
                검색 초기화
              </button>
            )}
          </div>
        ) : (
          <div className="automation-table">
            <table className="automation-table-content">
              <thead>
                <tr>
                  <th 
                    className={`sortable ${sortBy === 'name' ? sortOrder : ''}`}
                    onClick={() => handleSort('name')}
                  >
                    테스트명 {sortBy === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th 
                    className={`sortable ${sortBy === 'test_type' ? sortOrder : ''}`}
                    onClick={() => handleSort('test_type')}
                  >
                    타입 {sortBy === 'test_type' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th 
                    className={`sortable ${sortBy === 'environment' ? sortOrder : ''}`}
                    onClick={() => handleSort('environment')}
                  >
                    환경 {sortBy === 'environment' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th 
                    className={`sortable ${sortBy === 'creator_name' ? sortOrder : ''}`}
                    onClick={() => handleSort('creator_name')}
                  >
                    작성자 {sortBy === 'creator_name' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th 
                    className={`sortable ${sortBy === 'assignee_name' ? sortOrder : ''}`}
                    onClick={() => handleSort('assignee_name')}
                  >
                    담당자 {sortBy === 'assignee_name' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th 
                    className={`sortable ${sortBy === 'created_at' ? sortOrder : ''}`}
                    onClick={() => handleSort('created_at')}
                  >
                    생성일 {sortBy === 'created_at' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th>작업</th>
                </tr>
              </thead>
              <tbody>
                {filteredTests.map(test => (
                  <tr 
                    key={test.id} 
                    className={`automation-table-row ${selectedTest && selectedTest.id === test.id ? 'selected' : ''}`}
                    onClick={() => toggleTestDetails(test)}
                  >
                    <td className="test-name-cell">
                      <div className="test-name-content">
                        <strong>{test.name}</strong>
                        {test.description && (
                          <div className="test-description">{test.description}</div>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className="test-type-badge">{test.test_type}</span>
                    </td>
                    <td>
                      <span className="environment-badge">{test.environment}</span>
                    </td>
                    <td>{test.creator_name || '-'}</td>
                    <td>{test.assignee_name || '-'}</td>
                    <td>{test.created_at ? new Date(test.created_at).toLocaleDateString('ko-KR') : '-'}</td>
                    <td className="action-cell" onClick={(e) => e.stopPropagation()}>
                      <div className="action-buttons">
                        {user && (user.role === 'admin' || user.role === 'user') && (
                          <button 
                            className="btn btn-automation btn-icon"
                            onClick={() => handleExecuteTest(test.id)}
                            title="자동화 실행"
                          >
                            🤖
                          </button>
                        )}
                        <button 
                          className="btn btn-details btn-icon"
                          onClick={() => toggleTestDetails(test)}
                          title="상세보기"
                        >
                          {selectedTest && selectedTest.id === test.id ? '📋' : '📄'}
                        </button>
                        {user && (user.role === 'admin' || user.role === 'user') && (
                          <button 
                            className="btn btn-edit-icon btn-icon"
                            onClick={() => handleEditClick(test)}
                            title="수정"
                          >
                            ✏️
                          </button>
                        )}
                        {user && user.role === 'admin' && (
                          <button 
                            className="btn btn-delete-icon btn-icon"
                            onClick={() => handleDeleteTest(test.id)}
                            title="삭제"
                          >
                            ✕
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 상세 정보 표시 */}
      {selectedTest && (
        <div className="automation-detail-section">
          <AutomationTestDetail 
            test={selectedTest}
            onClose={closeDetail}
            onRefresh={fetchAutomationTests}
          />
        </div>
      )}

      {/* 하단 전체 화면 구조 제거 */}
      {/* {showDetail && selectedTest && (
        <div className="automation-detail-bottom">
          <AutomationTestDetail 
            test={selectedTest}
            onClose={closeDetail}
            onRefresh={fetchAutomationTests}
          />
        </div>
      )} */}

      {/* 추가 모달 */}
      {showAddModal && (
        <div className="modal-overlay fullscreen-modal">
          <div className="modal fullscreen-modal-content">
            <div className="modal-header">
              <h3>자동화 테스트 추가</h3>
              <button 
                className="modal-close"
                onClick={() => setShowAddModal(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>테스트명 *</label>
                <input
                  type="text"
                  className="form-control"
                  value={newTest.name}
                  onChange={(e) => setNewTest({...newTest, name: e.target.value})}
                  placeholder="테스트명을 입력하세요"
                />
              </div>
              <div className="form-group">
                <label>설명</label>
                <textarea
                  className="form-control"
                  value={newTest.description}
                  onChange={(e) => setNewTest({...newTest, description: e.target.value})}
                  placeholder="테스트 설명을 입력하세요"
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label>테스트 타입 *</label>
                <select
                  className="form-control"
                  value={newTest.test_type}
                  onChange={(e) => setNewTest({...newTest, test_type: e.target.value})}
                >
                  <option value="playwright">Playwright</option>
                  <option value="selenium">Selenium</option>
                  <option value="cypress">Cypress</option>
                  <option value="puppeteer">Puppeteer</option>
                </select>
              </div>
              <div className="form-group">
                <label>스크립트 경로 *</label>
                <input
                  type="text"
                  className="form-control"
                  value={newTest.script_path}
                  onChange={(e) => setNewTest({...newTest, script_path: e.target.value})}
                  placeholder="스크립트 파일 경로를 입력하세요"
                />
              </div>
              <div className="form-group">
                <label>환경</label>
                <select
                  className="form-control"
                  value={newTest.environment}
                  onChange={(e) => setNewTest({...newTest, environment: e.target.value})}
                >
                  <option value="dev">DEV</option>
                  <option value="alpha">ALPHA</option>
                  <option value="production">PRODUCTION</option>
                </select>
              </div>
              <div className="form-group">
                <label>매개변수 (JSON)</label>
                <textarea
                  className="form-control"
                  value={newTest.parameters}
                  onChange={(e) => setNewTest({...newTest, parameters: e.target.value})}
                  placeholder='{"timeout": 30, "retries": 3}'
                  rows="5"
                />
              </div>
              {user && (user.role === 'admin' || user.role === 'user') && (
                <div className="form-group">
                  <label>담당자</label>
                  <select
                    className="form-control"
                    value={newTest.assignee_id || ''}
                    onChange={(e) => setNewTest({...newTest, assignee_id: e.target.value ? Number(e.target.value) : null})}
                  >
                    <option value="">담당자를 선택하세요</option>
                    {users.map(user => (
                      <option key={user.id} value={user.id}>
                        {user.username || user.first_name || user.email}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
            <div className="modal-actions">
              <button 
                className="btn btn-cancel"
                onClick={() => setShowAddModal(false)}
              >
                취소
              </button>
              <button 
                className="btn btn-save"
                onClick={handleAddTest}
              >
                추가
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 수정 모달 */}
      {showEditModal && editingTest && (
        <div className="modal-overlay fullscreen-modal">
          <div className="modal fullscreen-modal-content">
            <div className="modal-header">
              <h3>자동화 테스트 수정</h3>
              <button 
                className="modal-close"
                onClick={() => setShowEditModal(false)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>테스트명 *</label>
                <input
                  type="text"
                  className="form-control"
                  value={editingTest.name}
                  onChange={(e) => setEditingTest({...editingTest, name: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>설명</label>
                <textarea
                  className="form-control"
                  value={editingTest.description}
                  onChange={(e) => setEditingTest({...editingTest, description: e.target.value})}
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label>테스트 타입 *</label>
                <select
                  className="form-control"
                  value={editingTest.test_type}
                  onChange={(e) => setEditingTest({...editingTest, test_type: e.target.value})}
                >
                  <option value="playwright">Playwright</option>
                  <option value="selenium">Selenium</option>
                  <option value="cypress">Cypress</option>
                  <option value="puppeteer">Puppeteer</option>
                </select>
              </div>
              <div className="form-group">
                <label>스크립트 경로 *</label>
                <input
                  type="text"
                  className="form-control"
                  value={editingTest.script_path}
                  onChange={(e) => setEditingTest({...editingTest, script_path: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>환경</label>
                <select
                  className="form-control"
                  value={editingTest.environment}
                  onChange={(e) => setEditingTest({...editingTest, environment: e.target.value})}
                >
                  <option value="dev">DEV</option>
                  <option value="alpha">ALPHA</option>
                  <option value="production">PRODUCTION</option>
                </select>
              </div>
              <div className="form-group">
                <label>매개변수 (JSON)</label>
                <textarea
                  className="form-control"
                  value={editingTest.parameters}
                  onChange={(e) => setEditingTest({...editingTest, parameters: e.target.value})}
                  rows="5"
                />
              </div>
              {user && (user.role === 'admin' || user.role === 'user') && (
                <div className="form-group">
                  <label>담당자</label>
                  <select
                    className="form-control"
                    value={editingTest.assignee_id || ''}
                    onChange={(e) => setEditingTest({...editingTest, assignee_id: e.target.value ? Number(e.target.value) : null})}
                  >
                    <option value="">담당자를 선택하세요</option>
                    {users.map(user => (
                      <option key={user.id} value={user.id}>
                        {user.username || user.first_name || user.email}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
            <div className="modal-actions">
              <button 
                className="btn btn-cancel"
                onClick={() => setShowEditModal(false)}
              >
                취소
              </button>
              <button 
                className="btn btn-save"
                onClick={handleEditTest}
              >
                수정
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AutomationTestManager; 
