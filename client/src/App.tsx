import { useEffect } from 'react';
import { useFeedbackStore } from './stores/feedbackStore';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  const { fetchFeedback, fetchTopics, fetchTrends } = useFeedbackStore();

  useEffect(() => {
    // Initial data load
    fetchFeedback();
    fetchTopics();
    fetchTrends();
  }, [fetchFeedback, fetchTopics, fetchTrends]);

  return (
    <div className="App">
      <Dashboard />
    </div>
  );
}

export default App;
