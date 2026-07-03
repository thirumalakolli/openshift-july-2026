package org.tektutor;

import javax.jms.*;
import org.apache.activemq.artemis.jms.client.ActiveMQConnectionFactory;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class JmsProducer {
    public static void main(String[] args) throws Exception {
	// Use fully qualified service name for cross-namespace communication
        String brokerUrl = "tcp://amq-broker-core-0-svc.jms-demo.svc.cluster.local:61616";
        String user = System.getenv("AMQ_USER");
        String password = System.getenv("AMQ_PASSWORD");

        // Fallback values
        if (user == null) user = "gsFZ8w5b";
        if (password == null) password = "DtLY5U1h";

        System.out.println("Starting continuous producer in OpenShift...");
        System.out.println("Connecting to: " + brokerUrl);

        try (ActiveMQConnectionFactory cf = new ActiveMQConnectionFactory(brokerUrl, user, password);
             JMSContext context = cf.createContext()) {

            Queue queue = context.createQueue("order.queue");
            JMSProducer producer = context.createProducer();
            
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
            int messageCount = 1;
            
            while (true) {
                String timestamp = LocalDateTime.now().format(formatter);
                String messageText = String.format("Order #%d created at %s [from OpenShift]", messageCount, timestamp);
                
                producer.send(queue, messageText);
                System.out.println("Sent message " + messageCount + ": " + messageText);
                
                messageCount++;
                Thread.sleep(3000); // 3 seconds delay
            }
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
