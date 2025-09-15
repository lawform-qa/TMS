import { useState, useEffect } from 'react';

export const useTestCasePagination = (filteredTestCases = []) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  // 페이지네이션 정보 업데이트
  useEffect(() => {
    const total = filteredTestCases.length;
    setTotalItems(total);
    setTotalPages(Math.ceil(total / itemsPerPage));
    
    // 현재 페이지가 총 페이지 수를 초과하면 첫 페이지로 이동
    if (currentPage > Math.ceil(total / itemsPerPage)) {
      setCurrentPage(1);
    }
  }, [filteredTestCases, itemsPerPage, currentPage]);

  // 페이지네이션된 데이터 가져오기
  const getPaginatedTestCases = () => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filteredTestCases.slice(startIndex, endIndex);
  };

  // 페이지 변경 핸들러
  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  // 페이지 크기 변경 핸들러
  const handleItemsPerPageChange = (newItemsPerPage) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1); // 페이지 크기 변경 시 첫 페이지로 이동
  };

  return {
    currentPage,
    totalPages,
    totalItems,
    itemsPerPage,
    getPaginatedTestCases,
    handlePageChange,
    handleItemsPerPageChange
  };
};
