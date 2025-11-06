import { useFeedbackStore } from '../stores/feedbackStore';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const Dashboard = () => {
  const { feedbackItems, topicClusters, sentimentTrends, isLoading, error } = useFeedbackStore();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  const sentimentData = [
    { name: 'Positive', value: feedbackItems.filter(f => f.sentiment === 'positive').length },
    { name: 'Negative', value: feedbackItems.filter(f => f.sentiment === 'negative').length },
    { name: 'Neutral', value: feedbackItems.filter(f => f.sentiment === 'neutral').length },
  ];

  const COLORS = ['#00C49F', '#FF8042', '#FFBB28'];

  return (
    <div>
      <h1>AI Customer Insights Agent</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
        <div style={{ height: '300px' }}>
          <h3>Sentiment Distribution</h3>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={sentimentData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {sentimentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div style={{ height: '300px' }}>
          <h3>Sentiment Trends</h3>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sentimentTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="positive" stroke="#00C49F" />
              <Line type="monotone" dataKey="negative" stroke="#FF8042" />
              <Line type="monotone" dataKey="neutral" stroke="#FFBB28" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ height: '300px', marginBottom: '20px' }}>
        <h3>Topic Clusters</h3>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={topicClusters}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div>
        <h3>Recent Feedback ({feedbackItems.length} items)</h3>
        <div style={{ maxHeight: '400px', overflowY: 'scroll', border: '1px solid #ccc', padding: '10px' }}>
          {feedbackItems.slice(0, 20).map((item) => (
            <div key={item.id} style={{ marginBottom: '10px', padding: '10px', border: '1px solid #eee' }}>
              <div style={{ fontWeight: 'bold', color: item.sentiment === 'positive' ? 'green' : item.sentiment === 'negative' ? 'red' : 'gray' }}>
                {item.sentiment.toUpperCase()} - {item.topic_cluster}
              </div>
              <div>{item.text}</div>
              <div style={{ fontSize: '0.8em', color: '#666' }}>{new Date(item.created_at).toLocaleDateString()}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
